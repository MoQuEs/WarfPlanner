from abc import abstractmethod
from dataclasses import dataclass, field
from os.path import exists
from typing import Optional

from marshmallow_dataclass import class_schema

from Utils import (
    get_json_file_content,
    put_json_file_content,
    arknights_file,
    save_file,
    language_file,
    clamp,
    remove_duplicate,
    map_object
)


class Rarity:
    @staticmethod
    def all_as_tuple() -> [(str, int, str)]:
        return [
            (0, "sprite_item_r1", "TIER_1"),
            (1, "sprite_item_r2", "TIER_2"),
            (2, "sprite_item_r3", "TIER_3"),
            (3, "sprite_item_r4", "TIER_4"),
            (4, "sprite_item_r5", "TIER_5"),
            (5, "sprite_item_r6", "TIER_6"),
        ]

    @staticmethod
    def from_game_data(rarity: str | int) -> int:
        for rarity_id, rarity_icon_id, rarity_name in Rarity.all_as_tuple():
            if (
                    rarity_icon_id == str(rarity)
                    or rarity_name == str(rarity)
                    or (isinstance(rarity, int) and rarity_id == rarity)
            ):
                return rarity_id

        raise Exception("Unknown rarity %s" % rarity)


class Upgrade:
    @staticmethod
    def from_game_data(value: dict) -> dict[str, int]:
        cost = {}

        def add_cost(mid: str, count: int):
            if mid not in cost:
                cost[mid] = 0
            cost[mid] += count

        if isinstance(value, dict):
            for key in ["lvlUpCost", "levelUpCost", "itemCost", "evolveCost"]:
                if key in value:
                    for value_cost in value[key] if value[key] is not None else []:
                        add_cost(str(value_cost["id"]), int(value_cost["count"]))

        if isinstance(value, list):
            for value_cost in value:
                add_cost(str(value_cost["id"]), int(value_cost["count"]))

        return cost


@dataclass
class Skill:
    name: dict[str, str] = field(default_factory=dict)
    icon_id: str = field(default_factory=str)
    mastery: list[dict[str, int]] = field(default_factory=list)

    @staticmethod
    def from_game_data(value: dict) -> "Skill":
        self = Skill()
        self.icon_id = value["skillId"]

        if value["levelUpCostCond"] is not None:
            for phase_data in value["levelUpCostCond"]:
                self.mastery.append(Upgrade.from_game_data(phase_data))

        return self


@dataclass
class Module:
    name: dict[str, str] = field(default_factory=dict)
    icon_id: str = field(default_factory=str)
    mastery: list[dict[str, int]] = field(default_factory=list)

    @staticmethod
    def from_game_data(lang_id: str, value: dict) -> "Module":
        self = Module()
        self.name = {lang_id: value["uniEquipName"]}
        self.icon_id = value["uniEquipIcon"]

        if value["itemCost"] is not None:
            for mastery_cost in value["itemCost"].values():
                self.mastery.append(Upgrade.from_game_data(mastery_cost))

        return self


@dataclass
class CharacterLevelUpgrade:
    enabled: bool = field(default_factory=bool)
    elite_from: int = field(default_factory=int)
    elite_to: int = field(default_factory=int)
    level_from: int = field(default_factory=int)
    level_to: int = field(default_factory=int)


@dataclass
class CharacterUpgrade:
    enabled: bool = field(default_factory=bool)
    upgrade_from: int = field(default_factory=int)
    upgrade_to: int = field(default_factory=int)


@dataclass
class CharacterUpgrades:
    level: CharacterLevelUpgrade = field(default_factory=CharacterLevelUpgrade)
    all_skil_lvlup: CharacterUpgrade = field(default_factory=CharacterUpgrade)
    skills: dict[str, CharacterUpgrade] = field(default_factory=dict)
    modules: dict[str, CharacterUpgrade] = field(default_factory=dict)


@dataclass
class Character:
    id: str = field(default_factory=str)
    name: dict[str, str] = field(default_factory=dict)
    rarity: int = field(default_factory=int)
    elite: list[dict[str, int]] = field(default_factory=list)
    all_skil_lvlup: list[dict[str, int]] = field(default_factory=list)
    skills: dict[str, Skill] = field(default_factory=dict)
    modules: dict[str, Module] = field(default_factory=dict)

    @staticmethod
    def from_game_data(lang_id: str, cid: str, value: dict) -> "Character":
        self = Character()
        self.id = cid
        self.name = {lang_id: value["name"]}
        self.rarity = Rarity.from_game_data(value["rarity"])

        if value["phases"] is not None:
            for phase_data in value["phases"]:
                self.elite.append(Upgrade.from_game_data(phase_data))

        if value["allSkillLvlup"] is not None:
            for phase_data in value["allSkillLvlup"]:
                self.all_skil_lvlup.append(Upgrade.from_game_data(phase_data))

        if value["skills"] is not None:
            for skill_data in value["skills"]:
                skill = Skill.from_game_data(skill_data)
                self.skills[skill_data["skillId"]] = skill

        return self

    def get_name(self, lang_id: str) -> str:
        if lang_id in self.name:
            return self.name[lang_id]

        return list(self.name.values())[0]

    def get_materials_for_upgrade(self, data: "Arknights", upgrades: CharacterUpgrades) -> dict[str, int]:
        materials = {}

        def add_upgrade_material(m: str, c: int):
            print('add', m, c)
            if m not in materials:
                materials[m] = 0

            materials[m] += c

        def add_upgrade_materials(upgrade: dict[str, int]):
            for m, c in upgrade.items():
                add_upgrade_material(m, c)

        all_gold = 0
        all_exp = 0

        if upgrades.level.enabled:
            elite_max_lvs = data.upgrade_max_lv_phases.phases[self.rarity]
            elite_gold_costs = data.upgrade_gold_cost.phases[self.rarity]

            for elite, elite_upgrade in enumerate(self.elite):
                if upgrades.level.elite_from <= elite <= upgrades.level.elite_to:
                    if upgrades.level.elite_from != upgrades.level.elite_to:
                        add_upgrade_materials(elite_upgrade)

                        if elite > 0 and elite - 1 < len(elite_gold_costs) and elite != upgrades.level.elite_from:
                            all_gold += elite_gold_costs[elite - 1]
                            pass

                    gold_map = data.upgrade_gold_map.map[elite]
                    exp_map = data.upgrade_exp_map.map[elite]

                    min_level = 1
                    if upgrades.level.elite_from == elite:
                        min_level = max(upgrades.level.level_from, 0)

                    max_level = elite_max_lvs[elite]
                    if upgrades.level.elite_to == elite:
                        max_level = min(upgrades.level.level_to, elite_max_lvs[elite])

                    for lv in range(min_level, max_level):
                        lv -= 1

                        gold = gold_map[lv]
                        exp = exp_map[lv]
                        if gold > 0:
                            print('LV %d; LMD %d; EXP %d' % (lv, gold, exp))
                            all_gold += gold
                            all_exp += exp

        if upgrades.all_skil_lvlup.enabled:
            for level, level_upgrade in enumerate(self.all_skil_lvlup):
                if upgrades.all_skil_lvlup.upgrade_from <= level < upgrades.all_skil_lvlup.upgrade_to:
                    add_upgrade_materials(level_upgrade)

        for skill_id, skill in self.skills.items():
            if skill_id in upgrades.skills:
                for mastery, mastery_upgrade in enumerate(skill.mastery):
                    upgrade_skill = upgrades.skills[skill_id]
                    if upgrade_skill.enabled and upgrade_skill.upgrade_from <= mastery < upgrade_skill.upgrade_to:
                        add_upgrade_materials(mastery_upgrade)

        for module_id, module in self.modules.items():
            if module_id in upgrades.modules:
                for mastery, module_upgrade in enumerate(module.mastery):
                    upgrade_module = upgrades.modules[module_id]
                    if upgrade_module.enabled and upgrade_module.upgrade_from <= mastery < upgrade_module.upgrade_to:
                        add_upgrade_materials(module_upgrade)

        if all_gold > 0 or data.static_names["LMD"] in materials:
            add_upgrade_material(data.static_names["LMD"], all_gold)

        if all_exp > 0 or data.static_names["EXP"] in materials:
            add_upgrade_material(data.static_names["EXP"], all_exp)

        if data.static_names["EXP"] not in materials:
            pass

        for mat, needs in data.needs_additional_mats.items():
            if mat in materials:
                add_upgrade_materials(needs)

        return materials


@dataclass
class Material:
    id: str = field(default_factory=str)
    name: dict[str, str] = field(default_factory=dict)
    rarity: int = field(default_factory=int)
    craft_from: Optional[dict[str, int]] = field(default=None)

    @staticmethod
    def from_game_data(lang_id: str, mid: str, value: dict, craft_from: None | dict[str, int]) -> "Material":
        self = Material()
        self.id = mid
        self.name = {lang_id: value["name"]}
        self.rarity = Rarity.from_game_data(value["rarity"])
        self.craft_from = craft_from

        return self

    def get_name(self, lang_id: str) -> str:
        if lang_id in self.name:
            return self.name[lang_id]

        return list(self.name.values())[0]


@dataclass
class UpgradeMaxLvPhases:
    phases: list[list[int]] = field(default_factory=list)

    @staticmethod
    def from_game_data(value: dict) -> "UpgradeMaxLvPhases":
        self = UpgradeMaxLvPhases()
        self.phases = value["maxLevel"]

        return self


@dataclass
class UpgradeGoldCost:
    phases: list[list[int]] = field(default_factory=list)

    @staticmethod
    def from_game_data(value: dict) -> "UpgradeGoldCost":
        self = UpgradeGoldCost()
        self.phases = value["evolveGoldCost"]

        return self


@dataclass
class UpgradeExpMap:
    map: list[list[int]] = field(default_factory=list)

    @staticmethod
    def from_game_data(value: dict) -> "UpgradeExpMap":
        self = UpgradeExpMap()
        self.map = value["characterExpMap"]

        return self


@dataclass
class UpgradeGoldMap:
    map: list[list[int]] = field(default_factory=list)

    @staticmethod
    def from_game_data(value: dict) -> "UpgradeGoldMap":
        self = UpgradeGoldMap()
        self.map = value["characterUpgradeCostMap"]

        return self


class SaveLoad:
    @staticmethod
    def from_file(t: type, path: str):
        data_schema = class_schema(t)()
        self = data_schema.load(get_json_file_content(path))

        return self

    def to_file(self, t: type, path: str):
        data_schema = class_schema(t)()
        put_json_file_content(path, data_schema.dump(self), pretty=True)

    @staticmethod
    @abstractmethod
    def load():
        pass

    def reload(self):
        map_object(self, self.load())

    @abstractmethod
    def save(self):
        pass


@dataclass
class Arknights(SaveLoad):
    characters: dict[str, Character] = field(default_factory=dict)

    materials: dict[str, Material] = field(default_factory=dict)

    exp: dict[str, int] = field(default_factory=dict)

    upgrade_max_lv_phases: UpgradeMaxLvPhases = field(
        default_factory=UpgradeMaxLvPhases
    )
    upgrade_gold_cost: UpgradeGoldCost = field(default_factory=UpgradeGoldCost)
    upgrade_exp_map: UpgradeExpMap = field(default_factory=UpgradeExpMap)
    upgrade_gold_map: UpgradeGoldMap = field(default_factory=UpgradeGoldMap)

    static_names: dict[str, str] = field(default_factory=dict)
    needs_additional_mats: dict[str, dict[str, int]] = field(default_factory=dict)
    display_materials: list[dict[str, list[str]]] = field(default_factory=list)

    @staticmethod
    def load() -> "Arknights":
        return Arknights.from_file(Arknights, arknights_file())

    def save(self):
        self.to_file(Arknights, arknights_file())

    def add_character(self, character_id: str, lang_id: str, character: Character):
        if character_id not in self.characters:
            self.characters[character_id] = character
        else:
            self.characters[character_id].name[lang_id] = character.name[lang_id]

    def add_material(self, material_id: str, lang_id: str, material: Material):
        if material_id not in self.materials:
            self.materials[material_id] = material
        else:
            self.materials[material_id].name[lang_id] = material.name[lang_id]

    def get_material(self, mid: str) -> Material:
        for material_id, material in self.materials.items():
            if mid == material_id:
                return material

        raise Exception("Unknown material with id %s" % mid)

    def get_material_id_by_model_class(self, mmc: str) -> str:
        for material_id, material in self.materials.items():
            for name in material.name.values():
                if mmc.lower() == remove_duplicate(name.replace(" ", "-")).lower():
                    return material_id

        raise Exception("Unknown material with id %s" % mmc)

    def get_character(self, cid: str) -> Character:
        for character_id, character in self.characters.items():
            if cid == character_id:
                return character

        raise Exception("Unknown character with id %s" % cid)

    def get_materials_to_upgrade(
            self, characters: dict[str, CharacterUpgrades]
    ) -> dict[str, dict[str, int]]:
        upgrades = {
            "all": {},
        }

        for character_id, character_upgrades in characters.items():
            character = self.get_character(character_id)
            materials = character.get_materials_for_upgrade(self, character_upgrades)

            for material_id, material_count in materials.items():
                if material_id not in upgrades["all"]:
                    upgrades["all"][material_id] = 0

                upgrades["all"][material_id] += material_count

            upgrades[character_id] = materials

        return upgrades


@dataclass
class Save(SaveLoad):
    materials: dict[str, int] = field(default_factory=dict)
    upgrades: dict[str, CharacterUpgrades] = field(default_factory=dict)

    @staticmethod
    def load() -> "Save":
        if not exists(language_file()):
            Language().save()
        return Save.from_file(Save, save_file())

    def save(self):
        self.to_file(Save, save_file())


@dataclass
class Language(SaveLoad):
    language: str = "en_US"
    texts: dict[str, dict] = field(default_factory=dict)

    @staticmethod
    def load() -> "Language":
        return Language.from_file(Language, language_file())

    def save(self):
        self.to_file(Language, language_file())

    def get_text(self, key: str) -> str:
        return self.__get_text(self.language, key)

    def __get_text(self, language: str, key: str, return_key: bool = False) -> str:
        org_key = key

        key = key.lower()
        text = self.texts[language]
        for current_key in key.split("."):
            if current_key in text:
                text = text[current_key]
            else:
                if return_key:
                    return org_key
                else:
                    return self.__get_text("en_US", org_key, True)

        return text
