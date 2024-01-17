from dotenv import load_dotenv
from roboflow import Roboflow

from Utils import env, run_best

load_dotenv()


rf = Roboflow(api_key=env("ROBOFLOW.API_KEY"))
workspace = rf.workspace(env("ROBOFLOW.WORKSPACE"))
project = workspace.project(env("ROBOFLOW.PROJECT"))
version = project.version(8)

version.deploy(run_best("008__yolov8n_yaml__500__2024_01_13__02_50_24"))
