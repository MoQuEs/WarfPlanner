from atexit import register
from pprint import pprint
from logging import FileHandler, WARNING, INFO, NOTSET
from typing import Any

from dotenv import load_dotenv
from flask import Flask
from jinja2 import Environment, PackageLoader, select_autoescape
from .Config import Config
from .Types import Arknights, Save, Language
from .Utils import (
    static_dir,
    get_free_port,
    templates_dir,
    get_file_content,
    css_dir,
    pwd_dir,
    js_dir,
)

load_dotenv()
config: Config = Config()

arknights: Arknights = Arknights.load()
language: Language = Language.load()
language.lang = config.language()
save: Save = Save.load()
arknights.set_save(save)
register(save.save)
register(config.save)
tailwind_js: str = get_file_content(js_dir("tailwind.js"))
tailwind_css: str = get_file_content(css_dir("tailwind.css"))
is_dev: bool = config.environment() == "development"


def reload_init():
    global tailwind_js, tailwind_css, arknights, save, language, is_dev

    config.reload()
    arknights.reload()
    language.reload()
    save.reload()

    arknights.set_save(save)

    language.language = config.language()
    tailwind_js = get_file_content(js_dir("tailwind.js"))
    tailwind_css = get_file_content(css_dir("tailwind.css"))
    is_dev = config.environment() == "development"


app: Flask = Flask(language.get_text("title"), static_folder=static_dir())

file_handler: FileHandler = FileHandler(pwd_dir("app.log"))
file_handler.setLevel(NOTSET if is_dev else WARNING)
app.logger.addHandler(file_handler)
app.debug = True if is_dev else False


environment: Environment = Environment(
    loader=PackageLoader("templates", templates_dir()), autoescape=select_autoescape()
)


def template(name: str, **kwargs: Any) -> str:
    kwargs["arknights"] = arknights
    kwargs["save"] = save
    kwargs["language"] = language.lang
    kwargs["config"] = config

    kwargs["is_dev"] = config.environment() == "development"
    kwargs["tailwind_js"] = tailwind_js
    kwargs["tailwind_css"] = tailwind_css

    return environment.get_template(name + ".html").render(**kwargs)


environment.globals.update(i18t=language.get_text)
environment.globals.update(template=template)
environment.globals.update(pprint=pprint)
environment.globals.update(len=len)
environment.globals.update(abs=abs)

listen_addr: str = "127.0.0.1"
listen_port: int = get_free_port() if config.port() == 0 else config.port()
link: str = "http://%s:%d" % (listen_addr, listen_port)
