from glob import glob
from os.path import join
from pprint import pprint
from re import match
from typing import Any

from .Config import Config
from .Logger import info

from .Types import (
    Arknights,
    Module,
    Material,
    UpgradeGoldMap,
    UpgradeExpMap,
    UpgradeGoldCost,
    UpgradeMaxLvPhases,
    Character,
    Upgrade,
    Recruitment,
    AKAppData,
)

from .Utils import (
    download_file,
    get_json_file_content,
    modules_dir,
    materials_dir,
    avatars_dir,
    skills_dir,
    wait_for_all_downloads,
    ak_json_dir,
)


def arknights_data_generator(config: Config, arknights: Arknights, save: bool = False) -> Arknights:

    info("Downloading Arknights data...")

    yuanyan3060_arknightsgameresource = "https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main/%s"
    aceship_arknight_images = "https://raw.githubusercontent.com/Aceship/Arknight-Images/%s"

    for repository, app_package, app_lang, ocr_lang, app_type in [
        ("ArknightsGameData", "com.hypergryph.arknights", "zh_CN", "ch_sim", "chinese"),
        ("ArknightsGameData_YoStar", "com.YoStarEN.Arknights", "en_US", "en", "global"),
        ("ArknightsGameData_YoStar", "com.YoStarJP.Arknights", "ja_JP", "ja", "global"),
        ("ArknightsGameData_YoStar", "com.YoStarKR.Arknights", "ko_KR", "ko", "global"),
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
            # Recruitment tags
            "gacha_table.json",
        ]:
            download_file(
                "https://raw.githubusercontent.com/Kengxxiao/%s/master/%s/gamedata/excel/%s"
                % (repository, app_lang, file),
                ak_json_dir(app_lang, file),
                force=config.force_download_data(),
            )

        arknights.ak_app_data.append(AKAppData(repository, app_package, app_lang, ocr_lang, app_type))

    download_file(
        "https://gamepress.gg/arknights/sites/arknights/files/json/operator_json.json",
        ak_json_dir("gamepress", "operator_json.json"),
        force=config.force_download_data(),
    )

    download_file(
        "https://raw.githubusercontent.com/Aceship/AN-EN-Tags/master/json/tl-akhr.json",
        ak_json_dir("aceship", "tl-akhr.json"),
        force=config.force_download_data(),
    )

    wait_for_all_downloads()

    info("Generating Arknights data...")

    excel_glob_path = ak_json_dir("**")
    not_obtainable_exemption = ["char_512_aprot"]

    # Static data
    arknights.static_names = {
        "LMD": "4001",
        "EXP": "5001",
        "CHIPS_CATALYST": "32001",
        "RED_CERTS": "4006",
    }
    arknights.needs_additional_mats = {
        "3213": {"32001": 1},
        "3223": {"32001": 1},
        "3233": {"32001": 1},
        "3243": {"32001": 1},
        "3253": {"32001": 1},
        "3263": {"32001": 1},
        "3273": {"32001": 1},
        "3283": {"32001": 1},
        "32001": {"4006": 90},
        "mod_unlock_token": {"4006": 120},
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
    arknights.display_recruitment = {
        "recruitment.class": [1, 2, 3, 4, 5, 6, 7, 8],
        "recruitment.position": [9, 10],
        "recruitment.qualification": [17, 14, 11],
        "recruitment.affix": [12, 13, 15, 16, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28],
    }

    # Prepare gamepress data
    info("Processing gamepress data...")

    gamepress_operator_data = {}
    for operator in get_json_file_content(ak_json_dir("gamepress", "operator_json.json")):
        gamepress_operator_data[operator["title"][0]["value"]] = int(operator["nid"][0]["value"])

    # Skills
    skills: dict[str, dict[str, Any]] = {}
    for path in glob(join(excel_glob_path, "skill_table.json")):
        langId = match(r".*[\\\/]+([^\\\/]+)[\\\/]+skill_table.*", path).group(1)

        info("Processing %s" % path)

        full_json = get_json_file_content(path)
        for key, value in full_json.items():
            name = value["levels"][0]["name"]

            if key not in skills:
                skills[key] = {"name": {}, "icon_id": None}

            skills[key]["id"] = value["skillId"]
            skills[key]["name"][langId] = name
            skills[key]["icon_id"] = value["iconId"]

    # Modules
    modules: dict[str, dict[str, Any]] = {}
    for path in glob(join(excel_glob_path, "uniequip_table.json")):
        langId = match(r".*[\\\/]+([^\\\/]+)[\\\/]+uniequip_table.*", path).group(1)

        info("Processing %s" % path)

        full_json = get_json_file_content(path)
        for key, value in full_json["equipDict"].items():
            if value["type"] == "INITIAL":
                continue

            module = Module.from_game_data(langId, value)

            if value["charId"] not in modules:
                modules[value["charId"]] = {}

            if key not in modules[value["charId"]]:
                modules[value["charId"]][key] = module
            else:
                modules[value["charId"]][key].name[langId] = module.name[langId]

            download_file(
                aceship_arknight_images % "equip/icon/%s.png" % module.icon_id,
                modules_dir("%s.png" % module.icon_id),
                force=config.force_download_images(),
            )

    # Recruitment tags
    static_recruitment_tags = {
        "WARRIOR": 1,
        "SNIPER": 2,
        "TANK": 3,
        "MEDIC": 4,
        "SUPPORT": 5,
        "CASTER": 6,
        "SPECIAL": 7,
        "PIONEER": 8,
        "MELEE": 9,
        "RANGED": 10,
    }
    rarity_recruitment_tags = {
        1: 17,
        4: 14,
        5: 11,
    }
    for path in glob(join(excel_glob_path, "gacha_table.json")):
        langId = match(r".*[\\\/]+([^\\\/]+)[\\\/]+gacha_table.*", path).group(1)

        info("Processing %s" % path)

        full_json = get_json_file_content(path)
        for value in full_json["gachaTags"]:
            arknights.recruitment.add_tag(arknights.get_app_type_by_lang_id(langId), value["tagName"], value["tagId"])

    recruitment_operator_data: dict[str, set[str]] = {}
    for operator in get_json_file_content(ak_json_dir("aceship", "tl-akhr.json")):
        recruitment_operator_data[operator["id"]] = {"chinese", "global"}
        if "hidden" in operator and operator["hidden"]:
            recruitment_operator_data[operator["id"]].discard("chinese")
        if "globalHidden" in operator and operator["globalHidden"]:
            recruitment_operator_data[operator["id"]].discard("global")

    # Characters
    for json in ["character_table.json", "char_patch_table.json"]:
        for path in glob(join(excel_glob_path, json)):
            langId = match(r".*[\\\/]+([^\\\/]+)[\\\/]+(character_table|char_patch_table).*", path).group(1)

            info("Processing %s" % path)

            full_json = get_json_file_content(path)
            if "patchChars" in full_json:
                full_json = full_json["patchChars"]

            for key, value in full_json.items():
                if (value["isNotObtainable"] is True and key not in not_obtainable_exemption) or not key.startswith(
                    "char_"
                ):
                    continue

                character = Character.from_game_data(langId, key, value)

                character.app_type.add(arknights.get_app_type_by_lang_id(langId))
                if "" in character.app_type:
                    character.app_type.discard("")

                if character.get_name(langId) in gamepress_operator_data:
                    character.gamepress_id = gamepress_operator_data[character.get_name(langId)]

                if key in recruitment_operator_data:
                    character.recruitment.in_app_types = recruitment_operator_data[key]

                rarity_tag = None
                if character.rarity.rarity_id in rarity_recruitment_tags:
                    rarity_tag = rarity_recruitment_tags[character.rarity.rarity_id]

                character.recruitment.set_tags(
                    static_recruitment_tags[value["profession"]],
                    static_recruitment_tags[value["position"]],
                    [arknights.recruitment.search_tag_with_lang_id(langId, tag) for tag in value["tagList"]],
                    rarity_tag,
                )

                arknights.add_character(key, langId, character)
                if "en_US" not in character.name:
                    character.name["en_US"] = value["appellation"]

                download_file(
                    yuanyan3060_arknightsgameresource % "avatar/%s.png" % key,
                    avatars_dir("%s.png" % key),
                    force=config.force_download_images(),
                )

                for skill_id, character_skill in character.skills.items():
                    character_skill.name = skills[skill_id]["name"]
                    if skills[skill_id]["icon_id"] is not None:
                        character_skill.icon_id = skills[skill_id]["icon_id"]

                    download_file(
                        yuanyan3060_arknightsgameresource % "skill/skill_icon_%s.png" % character_skill.icon_id,
                        skills_dir("%s.png" % character_skill.icon_id),
                        force=config.force_download_images(),
                    )

                if key in modules:
                    character.modules = modules[key]

    # Materials crafting
    craft = {}
    for path in glob(join(excel_glob_path, "building_data.json")):
        _langId = match(r".*[\\\/]+([^\\\/]+)[\\\/]+building_data.*", path).group(1)

        info("Processing %s" % path)

        full_json = get_json_file_content(path)
        for _, value in full_json["workshopFormulas"].items():
            costs = value["costs"]
            if "goldCost" in value and value["goldCost"] > 0:
                costs.append({"id": arknights.static_names["LMD"], "count": value["goldCost"]})

            craft[value["itemId"]] = Upgrade.from_game_data(costs)

    # Materials
    for path in glob(join(excel_glob_path, "item_table.json")):
        langId = match(r".*[\\\/]+([^\\\/]+)[\\\/]+item_table.*", path).group(1)

        info("Processing %s" % path)

        full_json = get_json_file_content(path)
        for key, value in full_json["items"].items():
            if (
                not key.isnumeric()
                and key
                not in [
                    "mod_unlock_token",
                    "mod_update_token_2",
                    "mod_update_token_1",
                    "REP_COIN",
                    "CRISIS_SHOP_COIN",
                ]
                and value["itemType"] != "CLASSIC_SHD"
            ):
                continue

            material = Material.from_game_data(langId, key, value, craft[key] if key in craft else None)
            arknights.add_material(key, langId, material)

            download_file(
                yuanyan3060_arknightsgameresource % "item/%s.png" % value["iconId"],
                materials_dir("%s.png" % key),
                force=config.force_download_images(),
            )

        for key, value in full_json["expItems"].items():
            if not key.isnumeric():
                continue

            arknights.exp[key] = value["gainExp"]

    # Upgrade
    for path in glob(join(excel_glob_path, "gamedata_const.json")):
        _langId = match(r".*[\\\/]+([^\\\/]+)[\\\/]+gamedata_const.*", path).group(1)

        info("Processing %s" % path)

        full_json = get_json_file_content(path)
        arknights.upgrade_max_lv_phases = UpgradeMaxLvPhases.from_game_data(full_json)
        arknights.upgrade_gold_cost = UpgradeGoldCost.from_game_data(full_json)
        arknights.upgrade_exp_map = UpgradeExpMap.from_game_data(full_json)
        arknights.upgrade_gold_map = UpgradeGoldMap.from_game_data(full_json)

    # Output
    if save:
        arknights.save()

    return arknights
