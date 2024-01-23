from glob import glob
from json import load, dumps
from os import getcwd, makedirs, remove
from os.path import dirname, join, exists, isfile, isdir
from random import randint, choice
from re import sub, escape, IGNORECASE, match, findall
from shutil import rmtree
from socket import socket
from string import ascii_letters, digits
from typing import Any

from cv2 import imdecode, IMREAD_UNCHANGED, GaussianBlur
from numpy import ndarray, dtype, generic, uint8, frombuffer, ones_like
from requests import get

from ThreadPool import ThreadPool

download_file_pool = ThreadPool(20)


def get_free_port() -> int:
    sock = socket()
    sock.bind(("", 0))
    free_port = sock.getsockname()[1]
    sock.close()
    return int(free_port)


def mkdir(path: str):
    makedirs(path, exist_ok=True)


def mkdir_from_file(path: str):
    makedirs(dirname(path), exist_ok=True)


def __join(*paths: [str]) -> str:
    return str(join(*paths))


def pwd_dir(*paths: [str | int]) -> str:
    return str(__join(getcwd(), *paths))


def data_join(*paths: [str]) -> str:
    return pwd_dir("data", *paths)


def arknights_dir(*paths: [str]) -> str:
    return data_join("arknights", *paths)


def auto_labels_in_dir(*paths: [str]) -> str:
    return data_join("auto_labels_in", *paths)


def labels_to_generate() -> str:
    return get_file_content(auto_labels_in_dir("labels_to_generate")).strip()


def auto_labels_out_dir(*paths: [str]) -> str:
    return data_join("auto_labels_out", *paths)


def labels_dir(*paths: [str]) -> str:
    return data_join("labels", *paths)


def label_data(label: str) -> str:
    return labels_dir(label, "data.yaml")


def runs_dir(*paths: [str]) -> str:
    return data_join("runs", *paths)


def best_run(run: str) -> str:
    return runs_dir(run, "weights", "best.pt")


def model_args(run: str) -> str:
    return runs_dir(run, "args.yaml")


def testing_dir(*paths: [str]) -> str:
    return data_join("testing", *paths)


def testing_images_dir(*paths: [str]) -> str:
    return testing_dir("images", *paths)


def src_dir(*paths: [str]) -> str:
    return pwd_dir("src", *paths)


def static_dir(*paths: [str]) -> str:
    return src_dir("static", *paths)


def css_dir(*paths: [str]) -> str:
    return static_dir("css", *paths)


def images_dir(*paths: [str]) -> str:
    return static_dir("images", *paths)


def avatars_dir(*paths: [str]) -> str:
    return images_dir("avatars", *paths)


def materials_dir(*paths: [str]) -> str:
    return images_dir("materials", *paths)


def materials_background_dir(*paths: [str]) -> str:
    return images_dir("materials_background", *paths)


def modules_dir(*paths: [str]) -> str:
    return images_dir("modules", *paths)


def site_dir(*paths: [str]) -> str:
    return images_dir("site", *paths)


def skills_dir(*paths: [str]) -> str:
    return images_dir("skills", *paths)


def js_dir(*paths: [str]) -> str:
    return static_dir("js", *paths)


def templates_dir(*paths: [str]) -> str:
    return src_dir("templates", *paths)


def save_file() -> str:
    return src_dir("save.json")


def config_file() -> str:
    return src_dir("config.ini")


def arknights_file() -> str:
    return src_dir("arknights.json")


def language_file() -> str:
    return src_dir("language.json")


def get_file_content(path: str) -> str:
    with open(path, mode="r", encoding="UTF-8") as file:
        content = file.read()
    return content


def get_json_file_content(path: str):
    with open(path, mode="r", encoding="UTF-8") as file:
        content = load(file)
    return content


def put_file_content(path: str, text: str):
    with open(path, mode="w", encoding="UTF-8") as file:
        file.write(text)


def put_json_file_content(path: str, data, **kwargs):
    indent = 4 if kwargs.get("pretty", False) is True else None
    put_file_content(path, dumps(data, indent=indent))


def download_file(url: str, path: str, **kwargs) -> ThreadPool:
    def download():
        if not exists(path) or kwargs.get("force", False) is True:
            if kwargs.get("verbose", False) is True:
                print("Downloading %s to %s" % (url, path))

            mkdir_from_file(path)
            response = get(url, allow_redirects=True)
            if response.status_code >= 500:
                print("Error downloading %s" % url)
                return

            if response.status_code >= 400:
                print("Can't downloading %s" % url)
                return

            with open(path, "wb") as handler:
                handler.write(response.content)

    download_file_pool.add_task(download)

    return download_file_pool


def clamp(value, min_value, max_value):
    if value < min_value:
        return min_value
    elif value > max_value:
        return max_value
    else:
        return value


def pad_array(array: list, to_length: int, to_append) -> list:
    if len(array) >= to_length:
        return array

    for i in range(0, to_length):
        if i >= len(array):
            array.append(to_append)


def is_between_with_margin(value1, value2, margin):
    return value2 - margin <= value1 <= value2 + margin


def escape_re(text: str) -> str:
    return escape(text).replace("\\-", "-")


def remove_duplicate(text: str, character: str = "-") -> str:
    result = sub(r'' + character + '+', '-', text)
    return result


def get_image_from_url(url: str) -> ndarray | ndarray[Any, dtype[generic | generic]]:
    response = get(url).content
    np_arr = frombuffer(response, uint8)
    return imdecode(np_arr, IMREAD_UNCHANGED)


def get_random_image(width: int, height: int) -> ndarray | ndarray[Any, dtype[generic | generic]]:
    urls = [
        "https://picsum.photos/%d/%d" % (width, height),
        "https://source.unsplash.com/random/%dx%d" % (width, height),
        "https://loremflickr.com/%d/%d" % (width, height),
    ]

    return get_image_from_url(urls[randint(0, len(urls) - 1)])


def overlay_image(img, img_overlay, pos):
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


def add_blur(image, kernel: tuple | int = 5, sigma: tuple | float = 0):
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


def generate_random_string(length: int = 10, characters: str = ascii_letters + digits):
    return ''.join(choice(characters) for _ in range(length))


def get_mats_to_generate_auto_labels(
        arknights_data,
        fn_filter: callable = lambda data: True,
        ret_as_arr: bool = False
) -> list:
    data = []

    regexp = r"([a-z0-9-]+)[\r\n]+(\d+)[\r\n]+?(Over Represented|Under Represented)?"
    find = findall(regexp, labels_to_generate(), IGNORECASE)
    for (name, count, represented) in find:
        count = int(count)
        mid = arknights_data.get_material_id_by_model_class(name)

        ret_data = {
            "name": name,
            "mid": mid,
            "count": count,
            "represented": represented
        }
        if fn_filter(ret_data):
            if ret_as_arr:
                data.append([name, mid, count, represented])
            else:
                data.append(ret_data)

    return data


def delete_by_pattern(directory: str, search_pattern: str, filter_pattern: str):
    for path in glob(__join(directory, search_pattern)):
        if match(filter_pattern, path) is None:
            continue

        try:
            if isfile(path):
                remove(path)
            elif isdir(path):
                rmtree(path)
        except Exception as e:
            print(f"Error deleting {path}: {e}")


def clear_auto_labels_in_dir():
    delete_by_pattern(auto_labels_in_dir(), "*", r"^.*\.(png|je?pg)$")


def clear_auto_labels_out_dir():
    delete_by_pattern(auto_labels_out_dir(), "*", r"^.*(annotations|images|train|valid|data\.yaml)$")


def map_object(old: object, new: object):
    for key, value in old.__class__.__dict__.items():
        if not key.startswith("__"):
            setattr(old, key, getattr(new, key))

        if key == "__dataclass_fields__":
            for key2, value2 in value.items():
                if not key2.startswith("__"):
                    setattr(old, key2, getattr(new, key2))
