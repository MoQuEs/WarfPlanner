import re
from http import HTTPStatus
from pprint import pprint
from typing import NamedTuple, TypeAlias
from flask import Blueprint, redirect, Response, current_app, request
from .Init import arknights, save, template, reload_init, config
from .Utils import add_upgrade_material, clamp
from .Types import CharacterUpgrades, CharacterUpgrade, Character, Material

main_routes_blueprint: Blueprint = Blueprint("main", "main")


MaterialsToUpgrade: TypeAlias = list[dict[str, dict[str, dict[str, Material | int]]]]


class CharactersToUpgrade(NamedTuple):
    character: Character
    upgrades: CharacterUpgrades
    materials: dict[str, int]


@main_routes_blueprint.get("/")
def index_route() -> str | Response:
    return template("index", characters=characters(), upgrades=upgrades(), materials=materials())


@main_routes_blueprint.get("/favicon.ico")
def favicon_route() -> str | Response:
    return redirect("/static/images/site/favicon.ico", code=HTTPStatus.MOVED_PERMANENTLY)


@main_routes_blueprint.post("/reload")
def reload_route() -> str | Response:
    current_app.logger.info("Reloading")

    reload_init()

    return Response(status=HTTPStatus.OK)


@main_routes_blueprint.get("/characters")
def characters_route() -> str | Response:
    current_app.logger.info("Showing characters")

    return template("characters", characters=characters())


def characters() -> list[Character]:
    current_app.logger.info("Characters")

    characters_list = []

    for cid, character in arknights.characters.items():
        character.in_upgrades = cid in save.upgrades
        characters_list.append(character)

    return characters_list


@main_routes_blueprint.get("/materials")
def materials_route() -> str | Response:
    current_app.logger.info("Showing materials")
    return template("materials", sections=materials())


def materials() -> MaterialsToUpgrade:
    current_app.logger.info("Materials")

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

            section[display_group_name] = group

        sections.append(section)

    return sections


@main_routes_blueprint.post("/material/<mid>")
def material_update_route(mid: str) -> str | Response:
    current_app.logger.info("Material update")

    need = 0
    if "need" in request.args:
        need = int(request.args["need"])

    have = int(request.form["have"])

    save.materials[mid] = have
    save.save()

    return template("material", material=arknights.materials[mid], have=have, need=need, show_input=True)


@main_routes_blueprint.get("/upgrades")
def upgrades_route() -> str | Response:
    current_app.logger.info("Showing upgrades")
    return template("upgrades", characters_to_upgrade=upgrades())


def upgrades() -> list[CharactersToUpgrade]:
    current_app.logger.info("upgrades")

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
    current_app.logger.info("Adding upgrade for %s", cid)

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
    current_app.logger.info("Showing upgrade form for %s", cid)

    for _cid, upgrade in save.upgrades.items():
        if cid == _cid:
            character = arknights.characters[cid]
            return template("upgrade_form", character=character, upgrade=upgrade)

    return Response(status=HTTPStatus.NOT_FOUND)


@main_routes_blueprint.put("/upgrade/<cid>")
def upgrades_add_route(cid: str) -> str | Response:
    current_app.logger.info("Add upgrade for %s", cid)

    if cid in save.upgrades:
        return Response(status=HTTPStatus.CONFLICT)

    save.upgrades[cid] = CharacterUpgrades()
    save.save()
    return upgrade_form_route(cid)


@main_routes_blueprint.post("/upgrade/<cid>")
def upgrades_edit_route(cid: str) -> str | Response:
    current_app.logger.info("Saving upgrade for %s", cid)

    if cid not in save.upgrades:
        return Response(status=HTTPStatus.NOT_FOUND)

    character = arknights.characters[cid]

    upgrade = save.upgrades[cid]

    max_level_phases = arknights.upgrade_max_lv_phases.phases[character.rarity]

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
    current_app.logger.info("Toggled enables for %s", cid)

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
    current_app.logger.info("Deleting upgrade for %s", cid)

    if cid not in save.upgrades:
        return Response(status=HTTPStatus.NOT_FOUND)

    del save.upgrades[cid]
    save.save()

    return Response(status=HTTPStatus.OK)


@main_routes_blueprint.get("/import_export")
def import_export_route() -> str | Response:
    current_app.logger.info("Showing import/export")

    return template("import_export")


@main_routes_blueprint.post("/import/<import_type>")
def import_route(import_type: str) -> str | Response:
    current_app.logger.info("Import data")

    arknights.import_from(import_type, request.form[import_type])

    return template("import_export")


@main_routes_blueprint.get("/settings")
def settings_route() -> str | Response:
    current_app.logger.info("Showing settings")
    return template("settings")


@main_routes_blueprint.post("/settings")
def settings_change_route() -> str | Response:
    current_app.logger.info("Showing settings change")

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
    current_app.logger.info("Showing about")

    return template("about")
