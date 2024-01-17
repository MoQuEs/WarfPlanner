import re

from dotenv import load_dotenv
from roboflow import Roboflow

from Utils import env, join, labels_dir, mkdir, is_dir, escape_re

load_dotenv()


rf = Roboflow(api_key=env("ROBOFLOW.API_KEY"))
workspace = rf.workspace(env("ROBOFLOW.WORKSPACE"))
project = workspace.project(env("ROBOFLOW.PROJECT"))

for version in project.get_version_information():
    project_data = re.match(r"([^/]*)/([^/]*)/(\d+)", version["id"])
    if project_data is None:
        continue

    version_id = int(project_data.group(3))
    label_dir = labels_dir(project_data.group(3).zfill(3))

    if is_dir(label_dir):
        continue

    mkdir(label_dir)
    project.version(version_id).download("yolov8", label_dir, True)

    new_source = []
    data_file = join(label_dir, "data.yaml")
    with open(data_file, "r") as source:
        for line in source.readlines():
            line = str(line).rstrip()

            line = re.sub(
                r"^[ \t]*test: .*",
                "test: " + escape_re(join(label_dir, "test", "images")),
                line,
            )
            line = re.sub(
                r"^[ \t]*train: .*",
                "train: " + escape_re(join(label_dir, "train", "images")),
                line,
            )
            line = re.sub(
                r"^[ \t]*val: .*",
                "val: " + escape_re(join(label_dir, "valid", "images")),
                line,
            )

            new_source.append(line)

    with open(data_file, "w") as source:
        for line in new_source:
            source.write(line + "\n")
