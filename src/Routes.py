from http import HTTPStatus
from pprint import pprint

from flask import Blueprint, redirect, Response

from Init import data, saved_data, template, reload_init

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
    material_sections = []

    materials_to_upgrade = data.get_materials_to_upgrade(saved_data.upgrades)

    for planner_material_section in data.materials:
        material_section = {}
        for (
            planner_material_group_name,
            planner_material_group,
        ) in planner_material_section.items():
            material_group = {}
            for planner_material in planner_material_group:
                have = 0
                if planner_material in saved_data.materials:
                    have = saved_data.materials[planner_material]

                need = 0
                if planner_material in materials_to_upgrade["all"]:
                    need = materials_to_upgrade["all"][planner_material]

                material_group[planner_material] = {
                    "material": data.get_material(planner_material),
                    "have": have,
                    "need": need,
                }

            material_section[planner_material_group_name] = material_group

        material_sections.append(material_section)

    return template(
        "materials",
        material_sections=material_sections,
    )


@main.get("/upgrades")
def upgrades_route():
    upgrades_characters = []

    materials_to_upgrade = data.get_materials_to_upgrade(saved_data.upgrades)
    for cid, upgrade_data in saved_data.upgrades.items():
        character = data.get_character(cid)
        materials = materials_to_upgrade[cid]

        upgrades_characters.append(
            {
                "character": character,
                "upgrades": upgrade_data,
                "materials": materials,
            }
        )

    pprint(upgrades_characters)

    return template(
        "upgrades",
        upgrades_characters=upgrades_characters,
    )
