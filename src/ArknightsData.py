import glob
import re

from dotenv import load_dotenv

from Types import (
    Data,
    Module,
    Material,
    UpgradeGoldMap,
    UpgradeExpMap,
    UpgradeGoldCost,
    UpgradeMaxLvPhases,
    Character,
)
from Utils import (
    download_file,
    arknights_dir,
    env,
    join,
    download_file_pool,
    get_json_file_content,
    modules_dir,
    materials_dir,
    avatars_dir,
    skills_dir,
)

load_dotenv()

print("Downloading Arknights data...")
for repository, lang in [
    ("ArknightsGameData", "zh_CN"),
    ("ArknightsGameData_YoStar", "en_US"),
    ("ArknightsGameData_YoStar", "ja_JP"),
    ("ArknightsGameData_YoStar", "ko_KR"),
]:
    for file in [
        "char_patch_table.json",
        "character_table.json",
        "skill_table.json",
        "uniequip_table.json",
        "item_table.json",
        "gamedata_const.json",
    ]:
        download_file(
            "https://raw.githubusercontent.com/Kengxxiao/%s/master/%s/gamedata/excel/%s"
            % (repository, lang, file),
            arknights_dir("json", lang, file),
            force=env("ARKNIGHTS.FORCE_DOWNLOAD_DATA", False),
        )

download_file_pool.join()

print("Generating Arknights data...")

data = Data()
excel_glob_path = arknights_dir("json", "**")
not_obtainable_exemption = ["char_512_aprot"]


# Skills
skills = {}
for path in glob.glob(join(excel_glob_path, "skill_table.json")):
    lang = re.match(r".*[\\\/]+([^\\\/]+)[\\\/]+skill_table.*", path).group(1)

    print("Processing %s %s" % (path, lang))
    full_json = get_json_file_content(path)
    for key, value in full_json.items():
        name = value["levels"][0]["name"]

        if key not in skills:
            skills[key] = {"name": {}, "icon_id": None}

        skills[key]["name"][lang] = name
        skills[key]["icon_id"] = value["iconId"]


# Modules
modules = {}
for path in glob.glob(join(excel_glob_path, "uniequip_table.json")):
    lang = re.match(r".*[\\\/]+([^\\\/]+)[\\\/]+uniequip_table.*", path).group(1)

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
            force=env("ARKNIGHTS.FORCE_DOWNLOAD_IMAGES", False),
        )


# Characters
for json in ["character_table.json", "char_patch_table.json"]:
    for path in glob.glob(join(excel_glob_path, "character_table.json")):
        lang = re.match(r".*[\\\/]+([^\\\/]+)[\\\/]+character_table.*", path).group(1)

        print("Processing %s %s" % (path, lang))
        full_json = get_json_file_content(path)
        if "patchChars" in full_json:
            full_json = full_json["patchChars"]

        for key, value in full_json.items():
            if (
                value["isNotObtainable"] is True and key not in not_obtainable_exemption
            ) or not key.startswith("char_"):
                continue

            character = Character.from_game_data(lang, value)
            data.add_character(key, lang, character)

            download_file(
                "https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main/avatar/%s.png"
                % key,
                avatars_dir("%s.png" % key),
                force=env("ARKNIGHTS.FORCE_DOWNLOAD_IMAGES", False),
            )

            for skill_id, character_skill in character.skills.items():
                character_skill.name = skills[skill_id]["name"]
                if skills[skill_id]["icon_id"] is not None:
                    character_skill.icon_id = skills[skill_id]["icon_id"]

                download_file(
                    "https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main/skill/skill_icon_%s.png"
                    % character_skill.icon_id,
                    skills_dir("%s.png" % character_skill.icon_id),
                    force=env("ARKNIGHTS.FORCE_DOWNLOAD_IMAGES", False),
                )

            if key in modules:
                character.modules = modules[key]


# Items
for path in glob.glob(join(excel_glob_path, "item_table.json")):
    lang = re.match(r".*[\\\/]+([^\\\/]+)[\\\/]+item_table.*", path).group(1)

    print("Processing %s %s" % (path, lang))
    full_json = get_json_file_content(path)
    for key, value in full_json["items"].items():
        if not key.isnumeric() and key not in [
            "mod_unlock_token",
            "mod_update_token_2",
            "mod_update_token_1",
        ]:
            continue

        data.add_material(key, lang, Material.from_game_data(lang, value))

        download_file(
            "https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main/item/%s.png"
            % value["iconId"],
            materials_dir("%s.png" % key),
            force=env("ARKNIGHTS.FORCE_DOWNLOAD_IMAGES", False),
        )

    for key, value in full_json["expItems"].items():
        if not key.isnumeric():
            continue

        data.exp[key] = value["gainExp"]


# Upgrade
for path in glob.glob(join(excel_glob_path, "gamedata_const.json")):
    lang = re.match(r".*[\\\/]+([^\\\/]+)[\\\/]+gamedata_const.*", path).group(1)

    print("Processing %s %s" % (path, lang))
    full_json = get_json_file_content(path)
    data.upgrade_max_lv_phases = UpgradeMaxLvPhases.from_game_data(full_json)
    data.upgrade_gold_cost = UpgradeGoldCost.from_game_data(full_json)
    data.upgrade_exp_map = UpgradeExpMap.from_game_data(full_json)
    data.upgrade_gold_map = UpgradeGoldMap.from_game_data(full_json)


# Static data
data.static_names = {
    "LMD": "4001",
    "EXP": "5001",
    "CHIPS_CATALYST": "32001",
    "RED_CERTS": "4006",
}
data.exp_mats = ["2004", "2003", "2002", "2001"]
data.dual_chips = ["3213", "3223", "3233", "3243", "3253", "3263", "3273", "3283"]
data.display_materials = [
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
        "materials.??? 1": ["31074", "31073"],
        "materials.??? 2": ["31084", "31083"],
    },
    {
        "materials.t5_1": ["30125", "30135", "30115"],
        "materials.t5_2": ["30145", "30155"],
    },
    {
        "materials.vanguard_chip": ["3213", "3212", "3211"],
        "materials.guard_chip": ["3223", "3222", "3221"],
        "materials.defender_chip": ["3233", "3232", "3231"],
        "materials.sniper_chip": ["3243", "3242", "3241"],
        "materials.caster_chip": ["3253", "3252", "3251"],
        "materials.medic_chip": ["3263", "3262", "3261"],
        "materials.supporter_chip": ["3273", "3272", "3271"],
        "materials.specialist_chip": ["3283", "3282", "3281"],
    },
]


# Item backgrounds
# for rarity_id, rarity_icon_id, rarity_name in Rarity.all_as_tuple():
#     download_file(
#         "https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main/item_rarity_img/%s.png"
#         % rarity_icon_id,
#         materials_background_dir("%s.png" % rarity_icon_id),
#         force=env("ARKNIGHTS.FORCE_DOWNLOAD_IMAGES", False),
#     )


# Output
data.save()


print("Waiting for downloads to complete...")
download_file_pool.join()
