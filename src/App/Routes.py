import re
from http import HTTPStatus
from pprint import pprint
from typing import NamedTuple, TypeAlias
from flask import Blueprint, redirect, Response, request, send_file
from itertools import combinations

from .OCR import from_image
from .ADB import get_devices_with_ak, screenshot
from .ArknightsData import arknights_data_generator
from .Init import arknights, save, template, reload_init, config
from .Logger import info
from .Utils import add_upgrade_material, clamp, fonts_dir
from .Types import (
    CharacterUpgrades,
    CharacterUpgrade,
    Character,
    Material,
    ImportExport,
)

main_routes_blueprint: Blueprint = Blueprint("main", "main")
MaterialsToUpgrade: TypeAlias = list[dict[str, dict[str, dict[str, Material | int]]]]

recruitment_selected_tags: set[int] = set()
recruitment_lang: str = config.language()
recruitment_app_type: str = config.arknights_client()


class CharactersToUpgrade(NamedTuple):
    character: Character
    upgrades: CharacterUpgrades
    materials: dict[str, int]


@main_routes_blueprint.get("/")
def index_route() -> str | Response:
    return template("index", upgrades=upgrades(), characters=characters())


@main_routes_blueprint.get("/favicon.ico")
def favicon_route() -> str | Response:
    return redirect("/static/images/site/favicon.ico", code=HTTPStatus.MOVED_PERMANENTLY)


@main_routes_blueprint.get("/fonts/<path:font>")
def fonts_route(font: str) -> str | Response:
    return send_file(fonts_dir(font))


@main_routes_blueprint.post("/reload_app")
def reload_app_route() -> str | Response:
    info("Reloading")

    reload_init()

    return Response(status=HTTPStatus.OK)


@main_routes_blueprint.post("/regenerate_arknights_data")
def regenerate_arknights_data_route() -> str | Response:
    info("Download arknights data")

    arknights_data_generator(config, arknights)

    return Response(status=HTTPStatus.OK)


def characters() -> list[Character]:
    info("Characters")

    characters_list = []

    for cid, character in arknights.characters.items():
        character.in_upgrades = cid in save.upgrades
        characters_list.append(character)

    return characters_list


@main_routes_blueprint.get("/materials")
def materials_route() -> str | Response:
    info("Showing materials")
    return template("materials", sections=materials())


def materials() -> MaterialsToUpgrade:
    info("Materials")

    showed_materials = {}

    sections = []

    materials_to_upgrade = arknights.get_materials_for_upgrade(save.upgrades)
    sortedEXP = sorted(arknights.exp.items(), key=lambda x: x[1])[::-1]

    have_exp = 0
    for exp_id, exp in sortedEXP:
        if exp_id in save.materials:
            have_exp += save.materials[exp_id] * exp

    save.materials[arknights.static_names["EXP"]] = have_exp
    save.save()

    need_exp = 0
    if arknights.static_names["EXP"] in materials_to_upgrade["all"]:
        need_exp = materials_to_upgrade["all"][arknights.static_names["EXP"]] - have_exp
        for exp_id, exp in sortedEXP:
            if need_exp > 0:
                divided = need_exp // exp
                if divided > 0:
                    add_upgrade_material(materials_to_upgrade["all"], exp_id, divided)
                    need_exp -= divided * exp

    if need_exp > 0:
        add_upgrade_material(materials_to_upgrade["all"], sortedEXP[-1][0], 1)

    for display_section in arknights.display_materials:
        section = {}

        for display_group_name, display_group in display_section.items():
            group = {}

            for material_to_show in display_group:
                have = 0
                if material_to_show in save.materials:
                    have = save.materials[material_to_show]

                need = 0
                if material_to_show in materials_to_upgrade["all"]:
                    need = materials_to_upgrade["all"][material_to_show]

                group[material_to_show] = {
                    "material": arknights.materials[material_to_show],
                    "have": have,
                    "need": need,
                }

                showed_materials[material_to_show] = True

            section[display_group_name] = group

        sections.append(section)

    # Rest from arknights.materials
    section = {"materials.rest": {}}
    for mid, material in arknights.materials.items():
        if mid not in showed_materials:
            have = 0
            if mid in save.materials:
                have = save.materials[mid]

            need = 0
            if mid in materials_to_upgrade["all"]:
                need = materials_to_upgrade["all"][mid]

            section["materials.rest"][mid] = {
                "material": material,
                "have": have,
                "need": need,
            }
    sections.append(section)

    return sections


@main_routes_blueprint.post("/material/<mid>")
def material_update_route(mid: str) -> str | Response:
    info("Material update")

    need = 0
    if "need" in request.args:
        need = int(request.args["need"])

    have = int(request.form["have"])

    save.materials[mid] = have
    save.save()

    if "full_refresh" in request.args:
        return materials_route()

    return template(
        "material",
        material=arknights.materials[mid],
        have=have,
        need=need,
        show_input=True,
        can_craft=arknights.can_craft_material(mid),
    )


@main_routes_blueprint.post("/material/<mid>/craft")
def material_craft_route(mid: str) -> str | Response:
    info("Material update")

    need = 0
    if "need" in request.args:
        need = int(request.args["need"])

    arknights.craft_material(mid)

    if "full_refresh" in request.args:
        return materials_route()

    return template(
        "material",
        material=arknights.materials[mid],
        have=save.materials[mid],
        need=need,
        show_input=True,
        can_craft=arknights.can_craft_material(mid),
    )


@main_routes_blueprint.get("/upgrades")
def upgrades_route() -> str | Response:
    info("Showing upgrades")
    return template("upgrades", characters_to_upgrade=upgrades(), characters=characters())


def upgrades() -> list[CharactersToUpgrade]:
    info("upgrades")

    characters_to_upgrade = []

    for cid, upgrade_data in save.upgrades.items():
        character = arknights.characters[cid]
        characters_to_upgrade.append(
            CharactersToUpgrade(
                character,
                upgrade_data,
                character.get_materials_for_upgrade(arknights, upgrade_data),
            )
        )

    return characters_to_upgrade


@main_routes_blueprint.get("/upgrade/<cid>")
def upgrade_route(cid: str) -> str | Response:
    info("Adding upgrade for %s", cid)

    for _cid, upgrades in save.upgrades.items():
        if cid == _cid:
            character = arknights.characters[cid]
            return template(
                "upgrade",
                character=character,
                upgrades=upgrades,
                materials=character.get_materials_for_upgrade(arknights, upgrades),
            )

    return Response(status=HTTPStatus.NOT_FOUND)


@main_routes_blueprint.get("/upgrade/<cid>/form")
def upgrade_form_route(cid: str) -> str | Response:
    info("Showing upgrade form for %s", cid)

    for _cid, upgrade in save.upgrades.items():
        if cid == _cid:
            character = arknights.characters[cid]
            return template("upgrade_form", character=character, upgrade=upgrade)

    return Response(status=HTTPStatus.NOT_FOUND)


@main_routes_blueprint.put("/upgrade/<cid>")
def upgrades_add_route(cid: str) -> str | Response:
    info("Add upgrade for %s", cid)

    if cid in save.upgrades:
        return Response(status=HTTPStatus.CONFLICT)

    save.upgrades[cid] = CharacterUpgrades()
    save.save()
    return upgrade_form_route(cid)


@main_routes_blueprint.post("/upgrade/<cid>")
def upgrades_edit_route(cid: str) -> str | Response:
    info("Saving upgrade for %s", cid)

    if cid not in save.upgrades:
        return Response(status=HTTPStatus.NOT_FOUND)

    character = arknights.characters[cid]

    upgrade = save.upgrades[cid]

    max_level_phases = arknights.upgrade_max_lv_phases.phases[character.rarity.rarity_id]

    upgrade.level.elite_from = clamp(int(request.form["elite_from"]), 0, len(max_level_phases) - 1)
    upgrade.level.elite_to = clamp(
        int(request.form["elite_to"]),
        upgrade.level.elite_from,
        len(max_level_phases) - 1,
    )

    upgrade.level.level_from = clamp(int(request.form["level_from"]), 1, max_level_phases[upgrade.level.elite_from])

    min_level_to = upgrade.level.level_from if upgrade.level.elite_from == upgrade.level.elite_to else 1
    upgrade.level.level_to = clamp(
        int(request.form["level_to"]),
        min_level_to,
        max_level_phases[upgrade.level.elite_to],
    )

    upgrade.all_skil_lvlup.upgrade_from = clamp(int(request.form["all_skil_lvlup_from"]), 1, 7)
    upgrade.all_skil_lvlup.upgrade_to = clamp(
        int(request.form["all_skil_lvlup_to"]), upgrade.all_skil_lvlup.upgrade_from, 7
    )

    for form_id, form_value in request.form.items():
        form_group = re.match(r"(skill|module)-(.*)-(from|to)", form_id)
        form_value = int(form_value)

        if form_group is None:
            continue

        if form_group.group(1) == "module":
            if form_group.group(2) not in upgrade.modules:
                upgrade.modules[form_group.group(2)] = CharacterUpgrade()

            if form_group.group(3) == "from":
                upgrade.modules[form_group.group(2)].upgrade_from = form_value
            elif form_group.group(3) == "to":
                upgrade.modules[form_group.group(2)].upgrade_to = form_value

        elif form_group.group(1) == "skill":
            if form_group.group(2) not in upgrade.skills:
                upgrade.skills[form_group.group(2)] = CharacterUpgrade()

            if form_group.group(3) == "from":
                upgrade.skills[form_group.group(2)].upgrade_from = form_value
            elif form_group.group(3) == "to":
                upgrade.skills[form_group.group(2)].upgrade_to = form_value

    return upgrade_route(cid)


@main_routes_blueprint.post("/upgrade/<cid>/toggle/<toggle_type>")
def upgrades_toggle_route(cid: str, toggle_type: str) -> str | Response:
    info("Toggled enables for %s", cid)

    if cid not in save.upgrades:
        return Response(status=HTTPStatus.NOT_FOUND)

    if toggle_type not in ["enabled", "materials"]:
        return Response(status=HTTPStatus.BAD_REQUEST)

    if toggle_type == "enabled":
        save.upgrades[cid].enabled = not save.upgrades[cid].enabled
    elif toggle_type == "materials":
        save.upgrades[cid].materials = not save.upgrades[cid].materials

    save.save()

    return upgrade_route(cid)


@main_routes_blueprint.delete("/upgrade/<cid>")
def upgrades_delete_route(cid: str) -> str | Response:
    info("Deleting upgrade for %s", cid)

    if cid not in save.upgrades:
        return Response(status=HTTPStatus.NOT_FOUND)

    del save.upgrades[cid]
    save.save()

    return Response(status=HTTPStatus.OK)


@main_routes_blueprint.get("/recruitment")
def recruitment_route() -> str | Response:
    info("Showing recruitment")

    return template("recruitment", selected_tags=recruitment_selected_tags, recruitment_lang=recruitment_lang)


@main_routes_blueprint.delete("/recruitment")
def recruitment_clear_route() -> str | Response:
    info("Deleting recruitment")

    recruitment_selected_tags.clear()
    return recruitment_route()


@main_routes_blueprint.post("/recruitment/lang")
def recruitment_set_lang_route() -> str | Response:
    info("Updating recruitment")

    pprint(request.form)

    return recruitment_route()


@main_routes_blueprint.post("/recruitment/<tig>")
def recruitment_add_tag_route(tig: str) -> str | Response:
    info("Updating recruitment")

    tig = int(tig)

    if tig in recruitment_selected_tags:
        recruitment_selected_tags.remove(tig)
        return recruitment_route()

    if len(recruitment_selected_tags) >= 5:
        return Response(status=HTTPStatus.NOT_ACCEPTABLE)

    recruitment_selected_tags.add(tig)

    return recruitment_route()


def get_tags_from_adb():
    ret = []
    for device in get_devices_with_ak():
        result = from_image(screenshot(device.device), [device.ocr_language])

        tags: set[int] = set()
        tags_with_cords: dict[int, list[Character]] = {}
        for cords, tag, confidence in result:
            lang_tags = arknights.recruitment.tags[device.app_language]
            if tag in lang_tags:
                tid = lang_tags[tag]
                tags.add(tid)

                chars = []
                for cid, character in arknights.characters.items():
                    if (device.is_cn and character.recruitment.in_cn) or (
                        device.is_global and character.recruitment.in_global
                    ):
                        if tid in character.recruitment.tags:
                            chars.append(character)

                tags_with_cords[tid] = chars

        ret.append((tags, tags_with_cords))


def characters_by_tags(tags: set[int], app_type: str) -> dict[int, list[Character]]:
    chars = {}
    for tid in tags:
        chars[tid] = []
        for cid, character in arknights.characters.items():
            if (device.is_cn and character.recruitment.in_cn) or (device.is_global and character.recruitment.in_global):
                if tid in character.recruitment.tags:
                    chars.append(character)

    return chars


@main_routes_blueprint.get("/recruitment/from_adb")
def recruitment_from_adb_route() -> str | Response:
    for tags, tags_with_cords in get_tags_from_adb():
        comps_chars: dict[tuple, tuple[int, list[Character]]] = {}
        for combs_tags in list(combinations(tags, 1)) + list(combinations(tags, 2)) + list(combinations(tags, 3)):

            lowest_rarity = 6
            chars: list[Character] = []

            for tag in combs_tags:
                if len(chars) == 0:
                    chars.extend([char for char in tags_with_cords[tag]])
                    continue

                tmp = []
                for char in tags_with_cords[tag]:
                    for c in chars:
                        if char.id == c.id:
                            tmp.append(char)

                chars = tmp

            if len(chars) == 0:
                continue

            for char in chars:
                if char.rarity.rarity_display < lowest_rarity:
                    lowest_rarity = char.rarity.rarity_display

            comps_chars[combs_tags] = (lowest_rarity, chars)

        def custom_sort_function(element: tuple[tuple, tuple[int, list[Character]]]):
            return element[1][0]

        # tuple(map(lambda x: arknights.recruitment.get_tag_with_lang_id(app_language, x), i))
        comps_chars: list[tuple[tuple, tuple[int, list[Character]]]] = sorted(
            [(i, c) for i, c in comps_chars.items()],
            key=custom_sort_function,
            reverse=True,
        )

    return template("recruitment")


@main_routes_blueprint.get("/import_export")
def import_export_route() -> str | Response:
    info("Showing import/export")

    return template("import_export")


@main_routes_blueprint.get("/export/<export_system>/<export_type>")
def export_route(export_system: str, export_type: str) -> str | Response:
    info("Export data for %s and type %s" % (export_system, export_type))

    import_export = ImportExport()

    function_name = "%s_export_%s" % (export_system, export_type)
    if function_name not in import_export.allowed_exports:
        return Response(status=HTTPStatus.NOT_FOUND)

    export_value = (getattr(import_export, function_name))(arknights, save)

    return template(
        "import_export-export_textarea",
        export_system=export_system,
        export_value=export_value,
    )


@main_routes_blueprint.post("/import/<import_system>/<import_type>")
def import_route(import_system: str, import_type: str) -> str | Response:
    info("Import data for %s and type %s" % (import_system, import_type))

    import_export = ImportExport()

    function_name = "%s_import_%s" % (import_system, import_type)
    if function_name not in import_export.allowed_imports:
        return Response(status=HTTPStatus.NOT_FOUND)

    (getattr(import_export, function_name))(request.form[import_system], arknights, save)

    return template("import_export")


@main_routes_blueprint.get("/settings")
def settings_route() -> str | Response:
    info("Showing settings")
    return template("settings")


@main_routes_blueprint.post("/settings")
def settings_change_route() -> str | Response:
    info("Showing settings change")

    config.scale(int(request.form["scale"]))
    config.theme(request.form["theme"])
    config.language(request.form["language"])

    config.port(int(request.form["port"]))
    config.server(request.form["server"])
    config.environment(request.form["environment"])
    config.mode(request.form["mode"])

    config.force_download_data(request.form.get("force_download_data") == "1")
    config.force_download_images(request.form.get("force_download_images") == "1")

    config.save()

    return template("settings-form")


@main_routes_blueprint.get("/about")
def about_route() -> str | Response:
    info("Showing about")

    return template("about")
