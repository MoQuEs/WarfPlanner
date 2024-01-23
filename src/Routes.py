from http import HTTPStatus
from pprint import pprint

from flask import Blueprint, redirect, Response

from Init import arknights, save, template, reload_init

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
    reload_init()

    return Response(status=HTTPStatus.NO_CONTENT)


@main.get("/materials")
def materials_route():
    sections = []

    materials_to_upgrade = arknights.get_materials_to_upgrade(save.upgrades)

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
    upgrades_characters = []

    materials_to_upgrade = arknights.get_materials_to_upgrade(save.upgrades)
    for cid, upgrade_data in save.upgrades.items():
        character = arknights.get_character(cid)
        materials = materials_to_upgrade[cid]

        upgrades_characters.append(
            {
                "character": character,
                "upgrades": upgrade_data,
                "materials": materials,
            }
        )

    return template(
        "upgrades",
        upgrades_characters=upgrades_characters,
    )
