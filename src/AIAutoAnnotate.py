from autodistill.detection import CaptionOntology
from autodistill_yolov8 import YOLOv8Base
from dotenv import load_dotenv

try:
    from yaml import CLoader as Loader, load
except ImportError:
    from yaml import Loader, load

from Utils import auto_labels_in_dir, auto_labels_out_dir, best_run, model_args, clear_auto_labels_out_dir

load_dotenv()
clear_auto_labels_out_dir()

run = "008__yolov8x_yaml__2024_01_13__08_43_00"

model_args_yaml = load(open(model_args(run), 'r'), Loader=Loader)
label_data_yaml = load(open(model_args_yaml['data'], 'r'), Loader=Loader)

caption_ontology = {}
for label in label_data_yaml['names']:
    caption_ontology[label] = label

base_model = YOLOv8Base(
    ontology=CaptionOntology(caption_ontology),
    weights_path=best_run(run),
)

base_model.label(
    input_folder=auto_labels_in_dir(),
    extension="png",
    output_folder=auto_labels_out_dir(),
)
