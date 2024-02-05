import pprint
from http import HTTPStatus

from flask import Blueprint, redirect, Response, current_app, request

from Init import arknights, save, template, reload_init
from Utils import add_upgrade_material
from Types import CharacterUpgrades

main = Blueprint("main", "main")


@main.get("/")
def index_route():
    return template("index")


@main.get("/favicon.ico")
def favicon_route():
    return redirect(
        "/static/images/site/favicon.ico", code=HTTPStatus.MOVED_PERMANENTLY
    )


@main.get("/reload")
def reload_route():
    current_app.logger.info("Reloading")

    reload_init()

    return Response(status=HTTPStatus.OK)


@main.get("/materials")
def materials_route():
    current_app.logger.info("Showing materials")

    sections = []

    materials_to_upgrade = arknights.get_materials_for_upgrade(save.upgrades)
    sortedEXP = sorted(arknights.exp.items(), key=lambda x: x[1])[::-1]

    have_exp = 0
    for exp_id, exp in sortedEXP:
        if exp_id in save.materials:
            have_exp += save.materials[exp_id] * exp

    save.materials[arknights.static_names['EXP']] = have_exp
    save.save()

    need_exp = 0
    if arknights.static_names['EXP'] in materials_to_upgrade['all']:
        need_exp = materials_to_upgrade['all'][arknights.static_names['EXP']] - have_exp
        for exp_id, exp in sortedEXP:
            if need_exp > 0:
                divided = need_exp // exp
                if divided > 0:
                    add_upgrade_material(materials_to_upgrade['all'], exp_id, divided)
                    need_exp -= divided * exp

    if need_exp > 0:
        add_upgrade_material(materials_to_upgrade['all'], sortedEXP[-1][0], 1)

    for display_section in arknights.display_materials:
        section = {}

        for (display_group_name, display_group) in display_section.items():
            group = {}

            for material_to_show in display_group:
                have = 0
                if material_to_show in save.materials:
                    have = save.materials[material_to_show]

                need = 0
                if material_to_show in materials_to_upgrade["all"]:
                    need = materials_to_upgrade["all"][material_to_show]

                group[material_to_show] = {
                    "material": arknights.get_material(material_to_show),
                    "have": have,
                    "need": need,
                }

            section[display_group_name] = group

        sections.append(section)

    return template(
        "materials",
        sections=sections,
    )


@main.get("/upgrades")
def upgrades_route():
    current_app.logger.info("Showing upgrades")

    characters_to_upgrade = []

    for cid, upgrade_data in save.upgrades.items():
        character = arknights.characters[cid]
        characters_to_upgrade.append({
            "character": character,
            "upgrades": upgrade_data,
            "materials": character.get_materials_for_upgrade(arknights, upgrade_data),
        })

    return template("upgrades", characters_to_upgrade=characters_to_upgrade)


@main.get("/characters")
def characters_route():
    current_app.logger.info("Showing characters")

    characters = []

    for cid, character in arknights.characters.items():
        characters.append({
            "character": character,
            "in_upgrades": cid in save.upgrades,
        })

    return template(
        "characters",
        characters=characters,
    )


@main.get("/upgrade/<cid>")
def upgrade_route(cid: str):
    current_app.logger.info("Adding upgrade for %s", cid)

    for _cid, upgrades in save.upgrades.items():
        if cid == _cid:
            character = arknights.characters[cid]
            return template(
                "upgrade",
                character=character,
                upgrades=upgrades,
                materials=character.get_materials_for_upgrade(arknights, upgrades)
            )

    return Response(status=HTTPStatus.NOT_FOUND)


@main.get("/upgrade/form/<cid>")
def upgrade_form_route(cid: str):
    current_app.logger.info("Showing upgrade form for %s", cid)

    for _cid, upgrade in save.upgrades.items():
        if cid == _cid:
            character = arknights.characters[cid]
            return template(
                "upgrade_form",
                character=character,
                upgrade=upgrade
            )

    return Response(status=HTTPStatus.NOT_FOUND)


@main.put("/upgrade/<cid>")
def upgrades_add_route(cid: str):
    current_app.logger.info("Add upgrade for %s", cid)

    if cid in save.upgrades:
        return Response(status=HTTPStatus.CONFLICT)

    save.upgrades[cid] = CharacterUpgrades()
    save.save()
    return upgrade_form_route(cid)



@main.post("/upgrade/<cid>")
def upgrades_edit_route(cid: str):
    current_app.logger.info("Saving upgrade for %s", cid)

    pprint.pprint(request.form)

    return upgrade_route(cid)


@main.delete("/upgrade/<cid>")
def upgrades_delete_route(cid: str):
    current_app.logger.info("Deleting upgrade for %s", cid)

    if cid not in save.upgrades:
        return Response(status=HTTPStatus.NOT_FOUND)

    del save.upgrades[cid]
    save.save()

    return Response(status=HTTPStatus.OK)
