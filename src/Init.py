from pprint import pprint
from logging import FileHandler, WARNING, INFO
from dotenv import load_dotenv
from flask import Flask
from jinja2 import Environment, PackageLoader, select_autoescape

from Config import Config
from Types import Arknights, Save, Language
from Utils import static_dir, get_free_port, templates_dir, get_file_content, css_dir, pwd_dir, js_dir

load_dotenv()
config = Config()

arknights = Arknights.load()
language = Language.load()
language.language = config.language()
save = Save.load()
tailwind_js = get_file_content(js_dir("tailwind.js"))
tailwind_css = get_file_content(css_dir("tailwind.css"))
is_dev = config.environment() == "development"


def reload_init():
    global tailwind_js, tailwind_css, arknights, save, language, is_dev

    config.reload()
    arknights.reload()
    language.reload()
    save.reload()

    language.language = config.language()
    tailwind_js = get_file_content(js_dir("tailwind.js"))
    tailwind_css = get_file_content(css_dir("tailwind.css"))
    is_dev = config.environment() == "development"


app = Flask(language.get_text("title"), static_folder=static_dir())

file_handler = FileHandler(pwd_dir('app.log'))
file_handler.setLevel(INFO if is_dev else WARNING)
app.logger.addHandler(file_handler)


environment = Environment(
    loader=PackageLoader("templates", templates_dir()), autoescape=select_autoescape()
)


def template(name: str, **kwargs) -> str:
    kwargs["arknights"] = arknights
    kwargs["save"] = save

    kwargs["language"] = language.language
    kwargs["environment"] = config.environment()
    kwargs["is_dev"] = config.environment() == "development"
    kwargs["tailwind_js"] = tailwind_js
    kwargs["tailwind_css"] = tailwind_css

    return environment.get_template(name + ".html").render(**kwargs)


environment.globals.update(i18t=language.get_text)
environment.globals.update(template=template)
environment.globals.update(pprint=pprint)
environment.globals.update(len=len)

listen_addr = "127.0.0.1"
listen_port = get_free_port() if config.port() == 0 else config.port()
link = "http://%s:%d" % (listen_addr, listen_port)
