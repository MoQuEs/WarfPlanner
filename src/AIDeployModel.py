from os import getenv

from dotenv import load_dotenv
from roboflow import Roboflow

from Utils import runs_dir

load_dotenv()


rf = Roboflow(api_key=getenv("ROBOFLOW.API_KEY"))
workspace = rf.workspace(getenv("ROBOFLOW.WORKSPACE"))
project = workspace.project(getenv("ROBOFLOW.PROJECT"))
version = project.version(8)

version.deploy(
    "yolov8",
    runs_dir("008__yolov8n_yaml__500__2024_01_13__02_50_24"),
)
