import json
import os
import re
import socket

import requests

from ThreadPool import ThreadPool

download_file_pool = ThreadPool(20)


def env(key: str, default=None) -> str:
    return os.getenv(key, default)


def get_free_port() -> int:
    sock = socket.socket()
    sock.bind(("", 0))
    free_port = sock.getsockname()[1]
    sock.close()
    return int(free_port)


def cpu_count() -> int:
    return os.cpu_count()


def pwd() -> str:
    return os.getcwd()


def mkdir(path: str):
    os.makedirs(path, exist_ok=True)


def is_dir(path: str):
    os.path.isdir(path)


def mkdir_from_file(path: str):
    os.makedirs(dir_name(path), exist_ok=True)


def pwd_dir(*paths: [str | int]) -> str:
    return str(os.path.join(pwd(), *paths))


def join(*paths: [str]) -> str:
    return str(os.path.join(*paths))


def basename(path: str) -> str:
    return os.path.basename(path)


def dir_name(path: str) -> str:
    return os.path.dirname(path)


def data_join(*paths: [str]) -> str:
    return pwd_dir("data", *paths)


def arknights_dir(*paths: [str]) -> str:
    return data_join("arknights", *paths)


def auto_labels_in_dir(*paths: [str]) -> str:
    return data_join("auto_labels_in", *paths)


def auto_labels_out_dir(*paths: [str]) -> str:
    return data_join("auto_labels_out", *paths)


def src_dir(*paths: [str]) -> str:
    return pwd_dir("src", *paths)


def static_dir(*paths: [str]) -> str:
    return src_dir("static", *paths)


def arknights_data_file() -> str:
    return static_dir("arknightsData.json")


def planner_data_file() -> str:
    return static_dir("plannerData.json")


def saved_data_file() -> str:
    return static_dir("savedData.json")


def language_data_file() -> str:
    return static_dir("languageData.json")


def css_dir(*paths: [str]) -> str:
    return static_dir("css", *paths)


def js_dir(*paths: [str]) -> str:
    return static_dir("js", *paths)


def images_dir(*paths: [str]) -> str:
    return static_dir("images", *paths)


def avatars_dir(*paths: [str]) -> str:
    return images_dir("avatars", *paths)


def materials_dir(*paths: [str]) -> str:
    return images_dir("materials", *paths)


def materials_background_dir(*paths: [str]) -> str:
    return images_dir("materials_background", *paths)


def skills_dir(*paths: [str]) -> str:
    return images_dir("skills", *paths)


def modules_dir(*paths: [str]) -> str:
    return images_dir("modules", *paths)


def templates_dir(*paths: [str]) -> str:
    return src_dir("templates", *paths)


def labels_dir(*paths: [str]) -> str:
    return data_join("labels", *paths)


def label_data(label: str) -> str:
    return labels_dir(label, "data.yaml")


def runs_dir(*paths: [str]) -> str:
    return data_join("runs", *paths)


def best_run(run: str) -> str:
    return runs_dir(run, "weights", "best.pt")


def run_best(run: str) -> str:
    return runs_dir(run, "weights", "best.pt")


def testing_dir(*paths: [str]) -> str:
    return data_join("testing", *paths)


def testing_images_dir(*paths: [str]) -> str:
    return testing_dir("images", *paths)


def get_file_content(path: str) -> str:
    with open(path, mode="r", encoding="UTF-8") as file:
        content = file.read()
    return content


def get_json_file_content(path: str):
    with open(path, mode="r", encoding="UTF-8") as file:
        content = json.load(file)
    return content


def put_file_content(path: str, text: str):
    with open(path, mode="w", encoding="UTF-8") as file:
        file.write(text)


def put_json_file_content(path: str, data, **kwargs):
    indent = 4 if kwargs.get("pretty", False) is True else None
    put_file_content(path, json.dumps(data, indent=indent))


def download_file(url: str, path: str, **kwargs) -> ThreadPool:
    def download():
        if not os.path.exists(path) or kwargs.get("force", False) is True:
            if kwargs.get("verbose", False) is True:
                print("Downloading %s to %s" % (url, path))

            mkdir_from_file(path)
            response = requests.get(url, allow_redirects=True)
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


def escape_re(string: str) -> str:
    return re.escape(string).replace("\\-", "-")
