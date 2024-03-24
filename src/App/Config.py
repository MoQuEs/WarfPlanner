from configparser import ConfigParser
from os import getenv
from os.path import exists
from typing import Any

from .Utils import config_file


class Config:
    config: ConfigParser

    def __init__(self):
        self.config = self.default()
        self.load()

    @staticmethod
    def default() -> ConfigParser:
        config = ConfigParser(allow_no_value=True)

        is_prod = getenv("APP.ENVIRONMENT", "production") == "production"

        config.add_section("settings")
        config.set("settings", "scale", "1.0")
        config.set("settings", "theme", "dark")
        config.set("settings", "language", "en_US")

        config.add_section("app")
        config.set("app", "port", "0" if is_prod else "49650")
        config.set("app", "environment", "production" if is_prod else "development")
        config.set("app", "server", "waitress" if is_prod else "flask")
        config.set("app", "mode", "window" if is_prod else "browser")

        config.add_section("arknights")
        config.set("arknights", "force_download_data", "true")
        config.set("arknights", "force_download_images", "false")

        return config

    def load(self):
        if not exists(config_file()):
            self.save()

        self.config.read(config_file())

    def reload(self):
        self.load()

    def save(self):
        with open(config_file(), "w") as file:
            self.config.write(file)

    def __set_and_get(self, section: str, key: str, value: str | None = None) -> str:
        self.__set(section, key, value)
        return self.config.get(section, key)

    def __set_and_get_bool(self, section: str, key: str, value: bool | None = None) -> bool:
        self.__set(section, key, value)
        return self.config.getboolean(section, key)

    def __set_and_get_int(self, section: str, key: str, value: int | None = None) -> int:
        self.__set(section, key, value)
        return self.config.getint(section, key)

    def __set_and_get_float(self, section: str, key: str, value: float | None = None) -> float:
        self.__set(section, key, value)
        return self.config.getfloat(section, key)

    def __set(self, section: str, key: str, value: Any = None) -> None:
        if value is not None:
            self.config.set(section, key, str(value))
            self.save()

    # settings

    def scale(self, value: None | int = None) -> int:
        return self.__set_and_get_int("settings", "scale", value)

    def theme(self, value: None | str = None) -> str:
        return self.__set_and_get("settings", "theme", value)

    def language(self, value: None | str = None) -> str:
        return self.__set_and_get("settings", "language", value)

    def arknights_client(self, value: None | str = None) -> str:
        return self.__set_and_get("settings", "arknights_client", value)

    # app

    def port(self, value: None | int = None) -> int:
        return self.__set_and_get_int("app", "port", value)

    def server(self, value: None | str = None) -> str:
        return self.__set_and_get("app", "server", value)

    def environment(self, value: None | str = None) -> str:
        return self.__set_and_get("app", "environment", value)

    def mode(self, value: None | str = None) -> str:
        return self.__set_and_get("app", "mode", value)

    # arknights

    def force_download_data(self, value: None | bool = None) -> bool:
        return self.__set_and_get_bool("arknights", "force_download_data", value)

    def force_download_images(self, value: None | bool = None) -> bool:
        return self.__set_and_get_bool("arknights", "force_download_images", value)
