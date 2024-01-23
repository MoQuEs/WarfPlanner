from datetime import datetime
from multiprocessing import cpu_count

from dotenv import load_dotenv
from ultralytics import YOLO

from Utils import (
    runs_dir,
    label_data,
)

load_dotenv()


class Experiment:
    def __init__(self,
                 model_name: str = "yolov8n",  # model name
                 model_type: str = "yaml",  # model type
                 label: str = "011",  # label version
                 numbers_of_epochs: int = 500,  # number of epochs
                 batch: int = 8,  # batch size or list of sizes
                 device: list = [0, 1],  # GPU index or array of indexes (None for CPU)
                 verbose: bool = True,
                 seed: int = 0,
                 val: bool = True,
                 project: str = runs_dir(),
                 workers: int = cpu_count() * 2,
                 patience: int = 0,
                 imgsz: int = 640,
                 ):
        self.model_name = model_name
        self.model_type = model_type
        self.label = label
        self.numbers_of_epochs = numbers_of_epochs
        self.batch = batch
        self.device = device
        self.verbose = verbose
        self.seed = seed
        self.val = val
        self.project = project
        self.workers = workers
        self.patience = patience
        self.imgsz = imgsz

    def name(self):
        return "%s__%s_%s__%s" % (
            self.label,
            self.model_name,
            self.model_type,
            datetime.now().strftime("%Y_%m_%d__%H_%M_%S"),
        )


for model_name in ["n", "s", "m", "l", "x"]:
    for experiment in [Experiment(model_name="yolov8%s" % model_name)]:
        model = YOLO(experiment.model_name + "." + experiment.model_type, task="detect")
        model.train(
            data=label_data(experiment.label),
            epochs=experiment.numbers_of_epochs,
            batch=experiment.batch,
            device=experiment.device,
            verbose=experiment.verbose,
            seed=experiment.seed,
            val=experiment.val,
            project=experiment.project,
            name=experiment.name(),
            workers=experiment.workers,
            patience=experiment.patience,
            imgsz=experiment.imgsz
        )
