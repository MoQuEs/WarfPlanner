from pprint import pprint

from dotenv import load_dotenv
from flask import Flask
from jinja2 import Environment, PackageLoader, select_autoescape

from Config import Config
from Types import Arknights, Save, Language
from Utils import static_dir, get_free_port, templates_dir, get_file_content, css_dir

load_dotenv()
config = Config()

arknights = Arknights.load()
language = Language.load()
language.language = config.language()
save = Save.load()
tailwind_css = get_file_content(css_dir("tailwind.css"))


def reload_init():
    global tailwind_css, arknights, save, language

    config.reload()
    arknights.reload()
    language.reload()
    save.reload()

    language.language = config.language()
    tailwind_css = get_file_content(css_dir("tailwind.css"))


app = Flask(language.get_text("title"), static_folder=static_dir())

environment = Environment(
    loader=PackageLoader("templates", templates_dir()), autoescape=select_autoescape()
)


def template(name: str, **kwargs) -> str:
    kwargs["language"] = language.language
    kwargs["environment"] = config.environment()
    kwargs["is_dev"] = config.environment() == "development"
    kwargs["tailwind_css"] = tailwind_css

    return environment.get_template(name + ".html").render(**kwargs)


environment.globals.update(i18t=language.get_text)
environment.globals.update(template=template)
environment.globals.update(pprint=pprint)

listen_addr = "127.0.0.1"
listen_port = get_free_port() if config.port() == 0 else config.port()
link = "http://%s:%d" % (listen_addr, listen_port)
