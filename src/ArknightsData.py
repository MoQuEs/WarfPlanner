from glob import glob
from os.path import join
from re import match

from dotenv import load_dotenv

from Types import (
    Arknights,
    Module,
    Material,
    UpgradeGoldMap,
    UpgradeExpMap,
    UpgradeGoldCost,
    UpgradeMaxLvPhases,
    Character, Upgrade,
)
from Utils import (
    download_file,
    arknights_dir,
    download_file_pool,
    get_json_file_content,
    modules_dir,
    materials_dir,
    avatars_dir,
    skills_dir,
    getenv_bool
)

load_dotenv()

FORCE_DOWNLOAD_DATA = getenv_bool("ARKNIGHTS.FORCE_DOWNLOAD_DATA")
FORCE_DOWNLOAD_IMAGES = getenv_bool("ARKNIGHTS.FORCE_DOWNLOAD_IMAGES")

print("Downloading Arknights data...")
for repository, lang in [
    ("ArknightsGameData", "zh_CN"),
    ("ArknightsGameData_YoStar", "en_US"),
    ("ArknightsGameData_YoStar", "ja_JP"),
    ("ArknightsGameData_YoStar", "ko_KR"),
]:
    for file in [
        # Guard Amiya
        "char_patch_table.json",
        # Characters
        "character_table.json",
        # Skills
        "skill_table.json",
        # Modules
        "uniequip_table.json",
        # Materials
        "item_table.json",
        # Upgrade / Leveling
        "gamedata_const.json",
        # Materials upgrade
        "building_data.json",
    ]:
        download_file(
            "https://raw.githubusercontent.com/Kengxxiao/%s/master/%s/gamedata/excel/%s"
            % (repository, lang, file),
            arknights_dir("json", lang, file),
            force=FORCE_DOWNLOAD_DATA,
        )

download_file_pool.join()

print("Generating Arknights data...")

arknights = Arknights()
excel_glob_path = arknights_dir("json", "**")
not_obtainable_exemption = ["char_512_aprot"]
characters_static_en_names = {

}


# Static data
arknights.static_names = {
    "LMD": "4001",
    "EXP": "5001",
    "CHIPS_CATALYST": "32001",
    "RED_CERTS": "4006",
}
arknights.needs_additional_mats = {
    "3213": {
        "32001": 1,
        "4006": 90
    },
    "3223": {
        "32001": 1,
        "4006": 90
    },
    "3233": {
        "32001": 1,
        "4006": 90
    },
    "3243": {
        "32001": 1,
        "4006": 90
    },
    "3253": {
        "32001": 1,
        "4006": 90
    },
    "3263": {
        "32001": 1,
        "4006": 90
    },
    "3273": {
        "32001": 1,
        "4006": 90
    },
    "3283": {
        "32001": 1,
        "4006": 90
    },
    "mod_unlock_token": {
        "4006": 120
    }
}
arknights.display_materials = [
    {
        "materials.main": ["4001", "5001", "32001", "4006"],
        "materials.module": [
            "mod_unlock_token",
            "mod_update_token_2",
            "mod_update_token_1",
        ],
        "materials.exp": ["2004", "2003", "2002", "2001"],
        "materials.skill": ["3303", "3302", "3301"],
    },
    {
        "materials.orirock": ["30014", "30013", "30012", "30011"],
        "materials.sugar": ["30024", "30023", "30022", "30021"],
        "materials.polyester": ["30034", "30033", "30032", "30031"],
        "materials.oriron": ["30044", "30043", "30042", "30041"],
        "materials.keton": ["30054", "30053", "30052", "30051"],
        "materials.device": ["30064", "30063", "30062", "30061"],
    },
    {
        "materials.salt": ["31064", "31063"],
        "materials.kohl": ["30074", "30073"],
        "materials.grindstone": ["30094", "30093"],
        "materials.rma70": ["30104", "30103"],
        "materials.solvent": ["31044", "31043"],
        "materials.gel": ["31014", "31013"],
        "materials.cutting_fluid": ["31054", "31053"],
        "materials.alloy": ["31024", "31023"],
        "materials.manganese": ["30084", "30083"],
        "materials.crystalline": ["31034", "31033"],
        "materials.???_1": ["31074", "31073"],
        "materials.???_2": ["31084", "31083"],
    },
    {
        "materials.t5_1": ["30125", "30135", "30115"],
        "materials.t5_2": ["30145", "30155"],
    },
    {
        "materials.vanguard_chips": ["3213", "3212", "3211"],
        "materials.guard_chips": ["3223", "3222", "3221"],
        "materials.defender_chips": ["3233", "3232", "3231"],
        "materials.sniper_chips": ["3243", "3242", "3241"],
        "materials.caster_chips": ["3253", "3252", "3251"],
        "materials.medic_chips": ["3263", "3262", "3261"],
        "materials.supporter_chips": ["3273", "3272", "3271"],
        "materials.specialist_chips": ["3283", "3282", "3281"],
    },
]


# Skills
skills = {}
for path in glob(join(excel_glob_path, "skill_table.json")):
    lang = match(r".*[\\\/]+([^\\\/]+)[\\\/]+skill_table.*", path).group(1)

    print("Processing %s %s" % (path, lang))
    full_json = get_json_file_content(path)
    for key, value in full_json.items():
        name = value["levels"][0]["name"]

        if key not in skills:
            skills[key] = {"name": {}, "icon_id": None}

        skills[key]["id"] = value["skillId"]
        skills[key]["name"][lang] = name
        skills[key]["icon_id"] = value["iconId"]


# Modules
modules = {}
for path in glob(join(excel_glob_path, "uniequip_table.json")):
    lang = match(r".*[\\\/]+([^\\\/]+)[\\\/]+uniequip_table.*", path).group(1)

    print("Processing %s %s" % (path, lang))
    full_json = get_json_file_content(path)
    for key, value in full_json["equipDict"].items():
        if value["type"] == "INITIAL":
            continue

        module = Module.from_game_data(lang, value)

        if value["charId"] not in modules:
            modules[value["charId"]] = {}

        if key not in modules[value["charId"]]:
            modules[value["charId"]][key] = module
        else:
            modules[value["charId"]][key].name[lang] = module.name[lang]

        download_file(
            "https://raw.githubusercontent.com/Aceship/Arknight-Images/main/equip/icon/%s.png"
            % module.icon_id,
            modules_dir("%s.png" % module.icon_id),
            force=FORCE_DOWNLOAD_IMAGES,
        )


# Characters
for json in ["character_table.json", "char_patch_table.json"]:
    for path in glob(join(excel_glob_path, "character_table.json")):
        lang = match(r".*[\\\/]+([^\\\/]+)[\\\/]+character_table.*", path).group(1)

        print("Processing %s %s" % (path, lang))
        full_json = get_json_file_content(path)
        if "patchChars" in full_json:
            full_json = full_json["patchChars"]

        for key, value in full_json.items():
            if (
                value["isNotObtainable"] is True and key not in not_obtainable_exemption
            ) or not key.startswith("char_"):
                continue

            character = Character.from_game_data(lang, key, value)
            arknights.add_character(key, lang, character)

            download_file(
                "https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main/avatar/%s.png"
                % key,
                avatars_dir("%s.png" % key),
                force=FORCE_DOWNLOAD_IMAGES,
            )

            for skill_id, character_skill in character.skills.items():
                character_skill.name = skills[skill_id]["name"]
                if skills[skill_id]["icon_id"] is not None:
                    character_skill.icon_id = skills[skill_id]["icon_id"]

                download_file(
                    "https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main/skill/skill_icon_%s.png"
                    % character_skill.icon_id,
                    skills_dir("%s.png" % character_skill.icon_id),
                    force=FORCE_DOWNLOAD_IMAGES,
                )

            if key in modules:
                character.modules = modules[key]


# Materials crafting
craft = {}
for path in glob(join(excel_glob_path, "building_data.json")):
    lang = match(r".*[\\\/]+([^\\\/]+)[\\\/]+building_data.*", path).group(1)

    print("Processing %s %s" % (path, lang))
    full_json = get_json_file_content(path)
    for _, value in full_json['workshopFormulas'].items():
        costs = value['costs']
        if 'goldCost' in value and value['goldCost'] > 0:
            costs.append({"id": arknights.static_names['LMD'], "count": value['goldCost']})

        craft[value['itemId']] = Upgrade.from_game_data(costs)


# Materials
for path in glob(join(excel_glob_path, "item_table.json")):
    lang = match(r".*[\\\/]+([^\\\/]+)[\\\/]+item_table.*", path).group(1)

    print("Processing %s %s" % (path, lang))
    full_json = get_json_file_content(path)
    for key, value in full_json["items"].items():
        if not key.isnumeric() and key not in [
            "mod_unlock_token",
            "mod_update_token_2",
            "mod_update_token_1",
        ]:
            continue

        material = Material.from_game_data(lang, key, value, craft[key] if key in craft else None)
        arknights.add_material(key, lang, material)

        download_file(
            "https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main/item/%s.png"
            % value["iconId"],
            materials_dir("%s.png" % key),
            force=FORCE_DOWNLOAD_IMAGES,
        )

    for key, value in full_json["expItems"].items():
        if not key.isnumeric():
            continue

        arknights.exp[key] = value["gainExp"]


# Upgrade
for path in glob(join(excel_glob_path, "gamedata_const.json")):
    lang = match(r".*[\\\/]+([^\\\/]+)[\\\/]+gamedata_const.*", path).group(1)

    print("Processing %s %s" % (path, lang))
    full_json = get_json_file_content(path)
    arknights.upgrade_max_lv_phases = UpgradeMaxLvPhases.from_game_data(full_json)
    arknights.upgrade_gold_cost = UpgradeGoldCost.from_game_data(full_json)
    arknights.upgrade_exp_map = UpgradeExpMap.from_game_data(full_json)
    arknights.upgrade_gold_map = UpgradeGoldMap.from_game_data(full_json)


# Output
arknights.save()


print("Waiting for downloads to complete...")
download_file_pool.join()
