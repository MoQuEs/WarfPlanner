from abc import abstractmethod
from dataclasses import dataclass, field

from marshmallow_dataclass import class_schema

from Utils import (
    get_json_file_content,
    put_json_file_content,
    arknights_data_file,
    saved_data_file,
    language_data_file,
    clamp,
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

        if isinstance(value, dict):
            for key in ["lvlUpCost", "levelUpCost", "itemCost", "evolveCost"]:
                if key in value:
                    for value_cost in value[key] if value[key] is not None else []:
                        cost[str(value_cost["id"])] = int(value_cost["count"])

        if isinstance(value, list):
            for value_cost in value:
                cost[str(value_cost["id"])] = int(value_cost["count"])

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
    name: dict[str, str] = field(default_factory=dict)
    rarity: int = field(default_factory=int)
    elite: list[dict[str, int]] = field(default_factory=list)
    all_skil_lvlup: list[dict[str, int]] = field(default_factory=list)
    skills: dict[str, Skill] = field(default_factory=dict)
    modules: dict[str, Module] = field(default_factory=dict)

    @staticmethod
    def from_game_data(lang_id: str, value: dict) -> "Character":
        self = Character()
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

    def get_materials_for_upgrade(
        self, data: "Data", upgrades: CharacterUpgrades
    ) -> dict[str, int]:
        materials = {}

        max_lvs = data.upgrade_max_lv_phases.phases[self.rarity]
        gold_costs = data.upgrade_gold_cost.phases[self.rarity]

        lmd = 0
        exp = 0

        if upgrades.level.enabled:
            for elite, elite_upgrade in enumerate(self.elite):
                if upgrades.level.elite_from <= elite <= upgrades.level.elite_to:
                    for material, cost in elite_upgrade.items():
                        if material not in materials:
                            materials[material] = 0

                        materials[material] += cost

                    if elite - 1 > 0:
                        lmd += (
                            gold_costs[elite - 1] if elite - 1 < len(gold_costs) else 0
                        )

                    min_c_level = clamp(upgrades.level.level_from, 0, max_lvs[elite])
                    max_c_level = clamp(upgrades.level.elite_to, 0, max_lvs[elite])
                    for level in range(
                        min_c_level if elite == upgrades.level.elite_from else 0,
                        max_c_level
                        if elite == upgrades.level.elite_to
                        else max_lvs[elite],
                    ):
                        lmd += data.upgrade_gold_map.map[elite][level]
                        exp += data.upgrade_exp_map.map[elite][level]

        if upgrades.all_skil_lvlup.enabled:
            for level, level_upgrade in enumerate(self.all_skil_lvlup):
                if (
                    upgrades.all_skil_lvlup.upgrade_from
                    <= level
                    <= upgrades.all_skil_lvlup.upgrade_to
                ):
                    for material, cost in level_upgrade.items():
                        if material not in materials:
                            materials[material] = 0

                        materials[material] += cost

        for skill_id, skill in self.skills.items():
            if skill_id in upgrades.skills:
                for mastery, mastery_upgrade in enumerate(skill.mastery):
                    if (
                        upgrades.skills[skill_id].enabled
                        and upgrades.skills[skill_id].upgrade_from
                        <= mastery
                        <= upgrades.skills[skill_id].upgrade_to
                    ):
                        for material, cost in mastery_upgrade.items():
                            if material not in materials:
                                materials[material] = 0

                            materials[material] += cost

        for module_id, module in self.modules.items():
            if module_id in upgrades.modules:
                for mastery, module_upgrade in enumerate(module.mastery):
                    if (
                        upgrades.modules[module_id].enabled
                        and upgrades.modules[module_id].upgrade_from
                        <= mastery
                        <= upgrades.modules[module_id].upgrade_to
                    ):
                        for material, cost in module_upgrade.items():
                            if material not in materials:
                                materials[material] = 0

                            materials[material] += cost

        if lmd > 0 or data.static_names["LMD"] in materials:
            if data.static_names["LMD"] not in materials:
                materials[data.static_names["LMD"]] = 0
            materials[data.static_names["LMD"]] += lmd

        if exp > 0 or data.static_names["EXP"] in materials:
            if data.static_names["EXP"] not in materials:
                materials[data.static_names["EXP"]] = 0
            materials[data.static_names["EXP"]] += exp

        if data.static_names["EXP"] not in materials:
            pass

        for dual_chip in data.dual_chips:
            if dual_chip in materials:
                if data.static_names["CHIPS_CATALYST"] not in materials:
                    materials[data.static_names["CHIPS_CATALYST"]] = 0

                if data.static_names["RED_CERTS"] not in materials:
                    materials[data.static_names["RED_CERTS"]] = 0

                materials[data.static_names["CHIPS_CATALYST"]] += materials[dual_chip]
                materials[data.static_names["RED_CERTS"]] += materials[dual_chip] * 90

        return materials


@dataclass
class Material:
    name: dict[str, str] = field(default_factory=dict)
    rarity: int = field(default_factory=int)

    @staticmethod
    def from_game_data(lang_id: str, value: dict) -> "Material":
        self = Material()
        self.name = {lang_id: value["name"]}
        self.rarity = Rarity.from_game_data(value["rarity"])

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
        new = self.load()

        for key, value in self.__class__.__dict__.items():
            if not key.startswith("__"):
                setattr(self, key, getattr(new, key))

    @abstractmethod
    def save(self):
        pass


@dataclass
class Data(SaveLoad):
    character: dict[str, Character] = field(default_factory=dict)

    material: dict[str, Material] = field(default_factory=dict)

    exp: dict[str, int] = field(default_factory=dict)

    upgrade_max_lv_phases: UpgradeMaxLvPhases = field(
        default_factory=UpgradeMaxLvPhases
    )
    upgrade_gold_cost: UpgradeGoldCost = field(default_factory=UpgradeGoldCost)
    upgrade_exp_map: UpgradeExpMap = field(default_factory=UpgradeExpMap)
    upgrade_gold_map: UpgradeGoldMap = field(default_factory=UpgradeGoldMap)

    static_names: dict[str, str] = field(default_factory=dict)
    exp_mats: list[str] = field(default_factory=list)
    dual_chips: list[str] = field(default_factory=list)
    display_materials: list[dict[str, list[str]]] = field(default_factory=list)

    @staticmethod
    def load() -> "Data":
        return Data.from_file(Data, arknights_data_file())

    def save(self):
        self.to_file(Data, arknights_data_file())

    def add_character(self, character_id: str, lang_id: str, character: Character):
        if character_id not in self.character:
            self.character[character_id] = character
        else:
            self.character[character_id].name[lang_id] = character.name[lang_id]

    def add_material(self, material_id: str, lang_id: str, material: Material):
        if material_id not in self.material:
            self.material[material_id] = material
        else:
            self.material[material_id].name[lang_id] = material.name[lang_id]

    def get_material(self, mid: str) -> Material:
        for material_id, material in self.material.items():
            if mid == material_id:
                return material

        raise Exception("Unknown material with id %s" % mid)

    def get_character(self, cid: str) -> Character:
        for character_id, character in self.character.items():
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
class SavedData(SaveLoad):
    materials: dict[str, int] = field(default_factory=dict)
    upgrades: dict[str, CharacterUpgrades] = field(default_factory=dict)

    @staticmethod
    def load() -> "SavedData":
        return SavedData.from_file(SavedData, saved_data_file())

    def save(self):
        self.to_file(SavedData, saved_data_file())


@dataclass
class LanguageData(SaveLoad):
    language: str = "en_US"
    texts: dict[str, dict] = field(default_factory=dict)

    @staticmethod
    def load() -> "LanguageData":
        return LanguageData.from_file(LanguageData, language_data_file())

    def save(self):
        self.to_file(LanguageData, language_data_file())

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
