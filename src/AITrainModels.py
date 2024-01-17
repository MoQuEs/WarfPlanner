import multiprocessing
from datetime import datetime

from dotenv import load_dotenv
from ultralytics import YOLO

from Utils import (
    runs_dir,
    label_data,
)

load_dotenv()

run_once = True
for model_size in ["n", "s", "m", "l", "x"]:
    # model = "yolov8%s" % model_size
    model = "yolov8n"  # model name
    model_type = "yaml"  # model type
    label = "010"  # label version

    numbers_of_epochs = 500  # number of epochs

    # 008__yolov8_yaml__500__2024_01_16__18_15_45
    experiment = "%s__%s_%s__%s__%s" % (
        label,
        model,
        model_type,
        numbers_of_epochs,
        datetime.now().strftime("%Y_%m_%d__%H_%M_%S"),
    )

    model = YOLO(model + "." + model_type, task="detect")
    model.train(
        data=label_data(label),
        epochs=numbers_of_epochs,
        batch=16,  # batch size or list of sizes
        device=[0, 1],  # GPU index or array of indexes (None for CPU)
        verbose=True,
        seed=0,
        val=True,
        project=runs_dir(),
        name=experiment,
        workers=multiprocessing.cpu_count() * 2,
        patience=0,
        imgsz=640,  # image size or array of x, y
    )

    if run_once:
        break
