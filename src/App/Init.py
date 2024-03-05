from os.path import exists
from atexit import register
from pprint import pprint
from logging import FileHandler, WARNING, INFO, NOTSET
from typing import Any

from dotenv import load_dotenv
from flask import Flask
from jinja2 import Environment, PackageLoader, select_autoescape

from .ArknightsData import arknights_data_generator
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
    arknights_file,
)

load_dotenv()

config: Config = Config()
is_dev: bool = config.environment() == "development"

language: Language = Language.load()
language.lang = config.language()

save: Save = Save.load()

if not exists(arknights_file()):
    arknights: Arknights = arknights_data_generator(config, Arknights())
else:
    arknights: Arknights = Arknights.load()
arknights.set_save(save)

register(save.save)
register(config.save)


def reload_init():
    global arknights, save, language, is_dev

    config.reload()
    is_dev = config.environment() == "development"

    language.reload()
    language.lang = config.language()

    save.reload()

    arknights.reload()
    arknights.set_save(save)


app: Flask = Flask(language.get_text("title"), static_folder=static_dir())

file_handler: FileHandler = FileHandler(pwd_dir("app.log"))
file_handler.setLevel(NOTSET if is_dev else WARNING)
app.logger.addHandler(file_handler)
app.debug = True if is_dev else False


environment: Environment = Environment(
    loader=PackageLoader("templates", templates_dir()), autoescape=select_autoescape()
)


def template(name: str, **kwargs: Any) -> str:
    kwargs["config"] = config
    kwargs["language"] = language.lang
    kwargs["save"] = save
    kwargs["arknights"] = arknights
    kwargs["is_dev"] = config.environment() == "development"

    return environment.get_template(name + ".html").render(**kwargs)


environment.globals.update(get_file_content=get_file_content)
environment.globals.update(js_dir=js_dir)
environment.globals.update(css_dir=css_dir)
environment.globals.update(i18t=language.get_text)
environment.globals.update(template=template)
environment.globals.update(pprint=pprint)
environment.globals.update(len=len)
environment.globals.update(abs=abs)

listen_addr: str = "127.0.0.1"
listen_port: int = get_free_port() if config.port() == 0 else config.port()
link: str = "http://%s:%d" % (listen_addr, listen_port)
