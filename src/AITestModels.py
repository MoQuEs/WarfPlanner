from glob import glob
from os.path import exists, basename
from re import search

from cv2 import imread, imwrite, rectangle, putText, FONT_HERSHEY_SIMPLEX
from dotenv import load_dotenv
from ultralytics import YOLO

from App.Utils import (
    testing_dir,
    runs_dir,
    testing_images_dir,
    best_run,
    mkdir,
)
from App.Image import add_box_to_image, Box, XYXY


def parse_result(directory: str, result) -> callable:
    boxes = []

    result_boxes = result.boxes.cpu().numpy()
    for index, xyxy in enumerate(result_boxes.xyxy):
        class_index = int(result_boxes.cls[index])
        class_name = result.names[class_index]

        overlap = False
        current_xyxy = XYXY(int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3]))
        for box in boxes:
            if box.xyxy.check_overlap_with_margin(current_xyxy):
                box.add_class(class_name)
                overlap = True
                break

        if not overlap:
            boxes.append(Box(current_xyxy, class_name))

    img = imread(result.path)
    for box in boxes:
        add_box_to_image(img, box)

    mkdir(testing_dir(directory))
    imwrite(testing_dir(directory, basename(result.path)), img)


def main() -> None:
    load_dotenv()

    for best in glob(runs_dir("**\\weights\\best.pt")):
        matched = search(r"([^\\\/]+)[\\\/]+weights[\\\/]+best\.pt", best)

        model = YOLO(best_run(matched.group(1)))
        for prediction in model.predict(
            [image for image in glob(testing_images_dir("*"))],
            verbose=False,
        ):
            if not exists(matched.group(1)):
                parse_result(matched.group(1), prediction)


if __name__ == "__main__":
    main()
