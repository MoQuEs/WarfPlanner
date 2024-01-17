import pprint

from flask import Flask
from jinja2 import Environment, PackageLoader, select_autoescape

from Config import Config
from Types import Data, SavedData, LanguageData
from Utils import static_dir, get_free_port, templates_dir, get_file_content, css_dir

config = Config()

data = Data.load()
language_data = LanguageData.load()
language_data.language = config.language()
saved_data = SavedData.load()
tailwind_css = get_file_content(css_dir("tailwind.css"))


def reload_init():
    global tailwind_css, data, saved_data, language_data

    config.load()
    data = data.load()
    language_data = language_data.load()
    language_data.language = config.language()
    saved_data = saved_data.load()
    tailwind_css = get_file_content(css_dir("tailwind.css"))


i18t = language_data.get_text


app = Flask(i18t("title"), static_folder=static_dir())

environment = Environment(
    loader=PackageLoader("templates", templates_dir()), autoescape=select_autoescape()
)


def template(name: str, **kwargs) -> str:
    kwargs["language"] = language_data.language
    kwargs["environment"] = config.environment()
    kwargs["is_dev"] = config.environment() == "development"
    kwargs["tailwind_css"] = tailwind_css

    return environment.get_template(name + ".html").render(**kwargs)


environment.globals.update(i18t=i18t)
environment.globals.update(template=template)
environment.globals.update(pprint=pprint.pprint)

listen_addr = "127.0.0.1"
listen_port = get_free_port() if config.port() == 0 else config.port()
link = "http://%s:%d" % (listen_addr, listen_port)
