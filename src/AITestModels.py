import glob
import re

import cv2
from dotenv import load_dotenv
from ultralytics import YOLO

from Utils import (
    testing_dir,
    basename,
    runs_dir,
    mkdir,
    is_between_with_margin,
    testing_images_dir,
    best_run,
)

load_dotenv()


class XYXY:
    def __init__(self, x0, y0, x1, y1):
        self.x0, self.y0, self.x1, self.y1 = x0, y0, x1, y1

    def check_overlap_with_margin(self, other):
        return (
            True
            if (
                is_between_with_margin(self.x0, other.x0, 30)
                and is_between_with_margin(self.y0, other.y0, 30)
                and is_between_with_margin(self.x1, other.x1, 30)
                and is_between_with_margin(self.y1, other.y1, 30)
            )
            else False
        )


class Box:
    def __init__(self, xyxy: XYXY, cls: str):
        self.xyxy = xyxy
        self.cls = [cls]

    def add_class(self, cls: str):
        self.cls.append(cls)


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

    img = cv2.imread(result.path)
    for box in boxes:
        add_box_to_image(img, box)

    mkdir(testing_dir(directory))
    cv2.imwrite(testing_dir(directory, basename(result.path)), img)


def add_box_to_image(img, box: Box):
    color = (255, 255, 255) if len(box.cls) == 1 else (0, 0, 255)

    cv2__box(img, box.xyxy, (0, 0, 0), 6)
    cv2__box(img, box.xyxy, color, 2)

    for index, cls in enumerate(box.cls):
        cv2__put_text__on_box(img, cls, box.xyxy, index, 0.5, (0, 0, 0), 6)
        cv2__put_text__on_box(img, cls, box.xyxy, index, 0.5, color, 2)


def cv2__box(img, xyxy, color, thickness):
    cv2.rectangle(
        img, (xyxy.x0, xyxy.y0), (xyxy.x1, xyxy.y1), color=color, thickness=thickness
    )


def cv2__put_text__on_box(img, cls, xyxy, index, font_scale, color, thickness):
    cv2.putText(
        img,
        cls,
        (xyxy.x0, xyxy.y0 + (25 * index) + 10),
        fontFace=cv2.FONT_HERSHEY_SIMPLEX,
        fontScale=font_scale,
        color=color,
        thickness=thickness,
    )


for best in glob.glob(runs_dir("**\\weights\\best.pt")):
    matched = re.search(r"([^\\\/]+)[\\\/]+weights[\\\/]+best\.pt", best)

    model = YOLO(best_run(matched.group(1)))
    for prediction in model.predict(
        [image for image in glob.glob(testing_images_dir("*"))],
        verbose=False,
    ):
        parse_result(matched.group(1), prediction)
