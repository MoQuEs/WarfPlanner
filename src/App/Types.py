from abc import abstractmethod
from dataclasses import dataclass, field, InitVar
from json import loads, dumps
from os.path import exists
from pprint import pprint
from typing import Optional, Any
from flask import current_app
from marshmallow_dataclass import class_schema
from .Utils import (
    get_json_file_content,
    put_json_file_content,
    arknights_file,
    save_file,
    language_file,
    add_upgrade_material,
    add_upgrade_materials,
    remove_duplicate,
    map_object,
)


class Rarity:
    @staticmethod
    def all_as_tuple() -> list[tuple[int, str, str]]:
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
    icon_id: str = field(default="")
    mastery: list[dict[str, int]] = field(default_factory=list)

    @staticmethod
    def from_game_data(value: dict) -> "Skill":
        self = Skill()
        self.icon_id = value["skillId"]

        if value["levelUpCostCond"] is not None:
            for phase_data in value["levelUpCostCond"]:
                self.mastery.append(Upgrade.from_game_data(phase_data))

        return self

    def get_name(self, lang_id: str) -> str:
        if lang_id in self.name:
            return self.name[lang_id]

        return list(self.name.values())[0]


@dataclass
class Module:
    name: dict[str, str] = field(default_factory=dict)
    icon_id: str = field(default="")
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

    def get_name(self, lang_id: str) -> str:
        if lang_id in self.name:
            return self.name[lang_id]

        return list(self.name.values())[0]


@dataclass
class CharacterLevelUpgrade:
    elite_from: int = field(default=0)
    elite_to: int = field(default=0)
    level_from: int = field(default=1)
    level_to: int = field(default=1)

    def is_enabled(self) -> bool:
        return self.elite_from != self.elite_to or self.level_from != self.level_to

    def __str__(self) -> str:
        return "E%d %d -> E%d %d" % (
            self.elite_from,
            self.level_from,
            self.elite_to,
            self.level_to,
        )


@dataclass
class CharacterUpgrade:
    upgrade_from: int = field(default=0)
    upgrade_to: int = field(default=0)

    def is_enabled(self) -> bool:
        return self.upgrade_from != self.upgrade_to

    def __str__(self) -> str:
        return "%d -> %d" % (self.upgrade_from, self.upgrade_to)


@dataclass
class CharacterUpgrades:
    enabled: bool = field(default=True)
    materials: bool = field(default=False)
    level: CharacterLevelUpgrade = field(default_factory=CharacterLevelUpgrade)
    all_skil_lvlup: CharacterUpgrade = field(default_factory=CharacterUpgrade)
    skills: dict[str, CharacterUpgrade] = field(default_factory=dict)
    modules: dict[str, CharacterUpgrade] = field(default_factory=dict)

    def __post_init__(self):
        self.all_skil_lvlup.upgrade_from = 1
        self.all_skil_lvlup.upgrade_to = 1


@dataclass
class Character:
    id: str = field(default="")
    name: dict[str, str] = field(default_factory=dict)
    rarity: int = field(default=1)
    elite: list[dict[str, int]] = field(default_factory=list)
    all_skil_lvlup: list[dict[str, int]] = field(default_factory=list)
    skills: dict[str, Skill] = field(default_factory=dict)
    modules: dict[str, Module] = field(default_factory=dict)

    cn_only: bool = field(default=True)

    @staticmethod
    def from_game_data(lang_id: str, cid: str, value: dict) -> "Character":
        self = Character()
        self.id = cid
        self.name = {lang_id: value["name"]}
        if "en_US" not in self.name:
            self.name["en_US"] = value["appellation"]
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

    def get_skill_name(self, sid: str, lang_id: str) -> str:
        if sid in self.skills:
            return self.skills[sid].get_name(lang_id)

        return sid

    def get_module_name(self, mid: str, lang_id: str) -> str:
        if mid in self.modules:
            return self.modules[mid].get_name(lang_id)

        return mid

    def get_skills(self) -> dict[str, Skill]:
        return self.skills

    def has_skills(self) -> bool:
        return len(self.skills) > 0

    def get_modules(self) -> dict[str, Module]:
        return self.modules

    def has_modules(self) -> bool:
        return len(self.modules) > 0

    def is_on_global(self) -> bool:
        return True if "en_US" in self.name else False

    def get_materials_for_upgrade(self, data: "Arknights", upgrades: CharacterUpgrades) -> dict[str, int]:
        materials: dict[str, int] = {}

        all_gold = 0
        all_exp = 0

        if upgrades.level.is_enabled():
            elite_max_lvs = data.upgrade_max_lv_phases.phases[self.rarity]
            elite_gold_costs = data.upgrade_gold_cost.phases[self.rarity]

            for elite, elite_upgrade in enumerate(self.elite):
                if upgrades.level.elite_from < elite and upgrades.level.elite_from != upgrades.level.elite_to:
                    add_upgrade_materials(materials, elite_upgrade)

                    if elite > 0 and elite - 1 < len(elite_gold_costs) and elite != upgrades.level.elite_from:
                        all_gold += elite_gold_costs[elite - 1]

                if upgrades.level.elite_from <= elite <= upgrades.level.elite_to:
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
                            all_gold += gold
                            all_exp += exp

        if upgrades.all_skil_lvlup.is_enabled():
            for level, level_upgrade in enumerate(self.all_skil_lvlup):
                if upgrades.all_skil_lvlup.upgrade_from <= level + 1 < upgrades.all_skil_lvlup.upgrade_to:
                    add_upgrade_materials(materials, level_upgrade)

        for skill_id, skill in self.skills.items():
            if skill_id in upgrades.skills:
                for mastery, mastery_upgrade in enumerate(skill.mastery):
                    upgrade_skill = upgrades.skills[skill_id]
                    if upgrade_skill.is_enabled() and upgrade_skill.upgrade_from <= mastery < upgrade_skill.upgrade_to:
                        add_upgrade_materials(materials, mastery_upgrade)

        for module_id, module in self.modules.items():
            if module_id in upgrades.modules:
                for mastery, module_upgrade in enumerate(module.mastery):
                    upgrade_module = upgrades.modules[module_id]
                    if (
                        upgrade_module.is_enabled()
                        and upgrade_module.upgrade_from <= mastery < upgrade_module.upgrade_to
                    ):
                        add_upgrade_materials(materials, module_upgrade)

        if all_gold > 0 or data.static_names["LMD"] in materials:
            add_upgrade_material(materials, data.static_names["LMD"], all_gold)

        if all_exp > 0 or data.static_names["EXP"] in materials:
            add_upgrade_material(materials, data.static_names["EXP"], all_exp)

        for mat, needs in materials.copy().items():
            req = self.get_sub_materials(data, mat, needs)
            add_upgrade_materials(materials, req)

        return materials

    def get_sub_materials(self, data: "Arknights", mid: str, count: int) -> dict[str, int]:
        materials: dict[str, int] = {}

        if mid in data.needs_additional_mats:
            for need, need_count in data.needs_additional_mats[mid].items():
                add_upgrade_material(materials, need, need_count * count)
                req = self.get_sub_materials(data, need, need_count * count)
                add_upgrade_materials(materials, req)

        return materials


@dataclass
class Material:
    id: str = field(default="")
    name: dict[str, str] = field(default_factory=dict)
    rarity: int = field(default=1)
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


# {
#   "@type":"@penguin-statistics/planner/config",
#   "items":[
#     {"id":"30135","have":1,"need":1},
#     {"id":"30043","have":1,"need":1},
#     {"id":"31043","have":1,"need":1},
#     ...
#   ],
#   "options":{
#     "byProduct":false,
#     "requireExp":false,
#     "requireLmb":false
#   },
#   "excludes":[]
# }
@dataclass
class PenguinStatistics:
    @staticmethod
    def export_data(arknights: "Arknights", save: "Save") -> str:
        upgrades = arknights.get_materials_for_upgrade(save.upgrades)

        data = {
            "@type": "@penguin-statistics/planner/config",
            "items": [],
            "options": {
                "byProduct": False,
                "requireExp": False,
                "requireLmb": False,
            },
            "excludes": [],
        }

        for mid, count in upgrades["all"].items():
            data["items"].append(
                {
                    "id": mid,
                    "have": 0,
                    "need": count,
                }
            )

        for mid, count in save.materials.items():
            data["items"].append(
                {
                    "id": mid,
                    "have": count,
                    "need": 0 if mid not in upgrades["all"] else upgrades["all"][mid],
                }
            )

        return dumps(data, indent=4)

    @staticmethod
    def import_data(data: str, arknights: "Arknights", save: "Save") -> None:
        data = loads(data)
        for item in data["items"]:
            mid = item["id"]

            if mid in arknights.materials:
                if mid not in save.materials:
                    save.materials[mid] = 0

                save.materials[mid] += item["have"]

        save.save()


# LMD,0
# Purchase Certificate,0
# Strategic Battle Record,0
# Tactical Battle Record,0
# Frontline Battle Record,0
# Drill Battle Record,0
# Skill Summary - 3,0
# Skill Summary - 2,0
# Skill Summary - 1,0
# ...
@dataclass
class GamePress:
    @staticmethod
    def export_data(arknights: "Arknights", save: "Save") -> str:
        upgrades = arknights.get_materials_for_upgrade(save.upgrades)

        data = ""
        for mid, count in save.materials.items():
            if mid in upgrades["all"]:
                data += "%s,%d\n" % (arknights.materials[mid].get_name("en_US"), count)

        return data

    @staticmethod
    def import_data(data: str, arknights: "Arknights", save: "Save") -> None:
        for line in data.split("\n"):
            if line.strip() == "":
                continue

            name, count = line.split(",")
            mid = arknights.get_material_id_by_model_class(name)
            save.materials[mid] = int(count)

        save.save()


class SaveLoad:
    @staticmethod
    def from_file(t: type, path: str) -> Any:
        data_schema = class_schema(t)()
        self = data_schema.load(get_json_file_content(path))

        return self

    def to_file(self, t: type, path: str) -> None:
        data_schema = class_schema(t)()
        put_json_file_content(path, data_schema.dump(self), pretty=True)

    @staticmethod
    @abstractmethod
    def load() -> Any:
        pass

    def reload(self) -> None:
        map_object(self, self.load())

    @abstractmethod
    def save(self) -> None:
        pass


@dataclass
class Arknights(SaveLoad):
    characters: dict[str, Character] = field(default_factory=dict)

    materials: dict[str, Material] = field(default_factory=dict)

    exp: dict[str, int] = field(default_factory=dict)

    upgrade_max_lv_phases: UpgradeMaxLvPhases = field(default=UpgradeMaxLvPhases())
    upgrade_gold_cost: UpgradeGoldCost = field(default=UpgradeGoldCost())
    upgrade_exp_map: UpgradeExpMap = field(default=UpgradeExpMap())
    upgrade_gold_map: UpgradeGoldMap = field(default=UpgradeGoldMap())

    static_names: dict[str, str] = field(default_factory=dict)
    needs_additional_mats: dict[str, dict[str, int]] = field(default_factory=dict)
    display_materials: list[dict[str, list[str]]] = field(default_factory=list)

    _save: "Save" = field(repr=False, init=False, default=None)

    @staticmethod
    def load() -> "Arknights":
        return Arknights.from_file(Arknights, arknights_file())

    def save(self) -> None:
        self.to_file(Arknights, arknights_file())

    def set_save(self, _save: "Save") -> None:
        self._save = _save

    def export_from(self, import_type: str) -> str:
        if import_type == "penguin-statistics":
            return PenguinStatistics.export_data(self, self._save)
        elif import_type == "gamepress":
            return GamePress.export_data(self, self._save)

    def import_from(
        self,
        import_type: str,
        data: str,
    ) -> None:
        if import_type == "penguin-statistics":
            PenguinStatistics.import_data(data, self, self._save)
        elif import_type == "gamepress":
            GamePress.import_data(data, self, self._save)

    def add_character(self, character_id: str, lang_id: str, character: Character) -> None:
        if character_id not in self.characters:
            self.characters[character_id] = character
        else:
            for lang, name in character.name.items():
                if lang not in self.characters[character_id].name:
                    self.characters[character_id].name[lang] = name
            self.characters[character_id].name[lang_id] = character.name[lang_id]

        if lang_id != "zh_CN":
            self.characters[character_id].cn_only = False

    def add_material(self, material_id: str, lang_id: str, material: Material) -> None:
        if material_id not in self.materials:
            self.materials[material_id] = material
        else:
            self.materials[material_id].name[lang_id] = material.name[lang_id]

    def get_material_id_by_model_class(self, mmc: str) -> str:
        for material_id, material in self.materials.items():
            for name in material.name.values():
                if mmc.lower() == remove_duplicate(name.replace(" ", "-")).lower():
                    return material_id

        raise Exception("Unknown material with id %s" % mmc)

    def get_materials_for_upgrade(self, characters: dict[str, CharacterUpgrades]) -> dict[str, dict[str, int]]:
        upgrades: dict[str, dict[str, int]] = {
            "all": {},
        }

        for cid, character_upgrades in characters.items():
            character = self.characters[cid]
            if not character_upgrades.enabled:
                continue

            materials = character.get_materials_for_upgrade(self, character_upgrades)
            add_upgrade_materials(upgrades["all"], materials)

            upgrades[cid] = materials

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

    def save(self) -> None:
        self.to_file(Save, save_file())


@dataclass
class Language(SaveLoad):
    lang: str = "en_US"
    texts: dict[str, dict] = field(default_factory=dict)

    @staticmethod
    def load() -> "Language":
        return Language.from_file(Language, language_file())

    def save(self) -> None:
        self.to_file(Language, language_file())

    def get_text(self, key: str) -> str:
        return self.__get_text(self.lang, key, False)

    def __get_text(self, language: str, key: str, return_key: bool = False) -> str:
        org_key = key

        key = key.lower()
        text = self.texts[language]
        for current_key in key.split("."):
            if current_key in text:
                text = text[current_key]
            else:
                if return_key or language == "en_US":
                    current_app.logger.warning("Unknown language key %s" % org_key)
                    return org_key
                else:
                    current_app.logger.warning(
                        "Try to use en_US language to get %s instead of %s" % (org_key, language)
                    )
                    return self.__get_text("en_US", org_key, True)

        return text
