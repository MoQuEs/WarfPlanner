from random import randint
from typing import Any
from requests import get
from cv2 import imdecode, IMREAD_UNCHANGED, GaussianBlur, rectangle, putText, FONT_HERSHEY_SIMPLEX
from numpy import ndarray, dtype, generic, uint8, frombuffer, ones_like
from .Utils import is_between_with_margin

Image = ndarray | ndarray[Any, dtype[generic | generic]]


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


def get_image_from_url(url: str) -> Image:
    response = get(url).content
    np_arr = frombuffer(response, uint8)
    return imdecode(np_arr, IMREAD_UNCHANGED)


def get_random_image(width: int, height: int) -> Image:
    urls = [
        "https://picsum.photos/%d/%d" % (width, height),
        "https://source.unsplash.com/random/%dx%d" % (width, height),
        "https://loremflickr.com/%d/%d" % (width, height),
    ]

    return get_image_from_url(urls[randint(0, len(urls) - 1)])


def overlay_image(img: Image, img_overlay: Image, pos: tuple[int, int]) -> None:
    x, y = pos

    # Overlay alpha channel ranges
    try:
        alpha_mask = img_overlay[:, :, 3] / 255.0
    except IndexError:
        alpha_mask = ones_like(img[:, :, 0])

    # Image ranges
    y1, y2 = max(0, y), min(img.shape[0], y + img_overlay.shape[0])
    x1, x2 = max(0, x), min(img.shape[1], x + img_overlay.shape[1])

    # Overlay ranges
    y1o, y2o = max(0, -y), min(img_overlay.shape[0], img.shape[0] - y)
    x1o, x2o = max(0, -x), min(img_overlay.shape[1], img.shape[1] - x)

    # Exit if nothing to do
    if y1 >= y2 or x1 >= x2 or y1o >= y2o or x1o >= x2o:
        return

    channels = img.shape[2]

    alpha = alpha_mask[y1o:y2o, x1o:x2o]
    alpha_inv = 1.0 - alpha

    for c in range(channels):
        img[y1:y2, x1:x2, c] = alpha * img_overlay[y1o:y2o, x1o:x2o, c] + alpha_inv * img[y1:y2, x1:x2, c]


def add_blur(image: Image, kernel: tuple | int = 5, sigma: tuple | float = 0) -> Image:
    if isinstance(kernel, int):
        kernel_size = (kernel, kernel)
    else:
        kernel_size = kernel

    if isinstance(sigma, float | int):
        sigmaX = float(sigma)
        sigmaY = float(sigma)
    else:
        sigmaX = float(sigma[0])
        sigmaY = float(sigma[1])

    return GaussianBlur(image, kernel_size, sigmaX, None, sigmaY)


def add_box_to_image(img, box: Box):
    color = (255, 255, 255) if len(box.cls) == 1 else (0, 0, 255)

    cv2__box(img, box.xyxy, (0, 0, 0), 6)
    cv2__box(img, box.xyxy, color, 2)

    for index, cls in enumerate(box.cls):
        cv2__put_text__on_box(img, cls, box.xyxy, index, 0.5, (0, 0, 0), 6)
        cv2__put_text__on_box(img, cls, box.xyxy, index, 0.5, color, 2)


def cv2__box(img, xyxy, color, thickness):
    rectangle(img, (xyxy.x0, xyxy.y0), (xyxy.x1, xyxy.y1), color=color, thickness=thickness)


def cv2__put_text__on_box(img, cls, xyxy, index, font_scale, color, thickness):
    putText(
        img,
        cls,
        (xyxy.x0, xyxy.y0 + (25 * index) + 10),
        fontFace=FONT_HERSHEY_SIMPLEX,
        fontScale=font_scale,
        color=color,
        thickness=thickness,
    )
