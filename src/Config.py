from configparser import ConfigParser
from os import getenv
from os.path import exists

from Utils import config_file


class Config:
    config: ConfigParser
    app_mode_default = "window"
    app_modes = ("window", "browser")
    app_environments = ("production", "development")
    settings_modes = ("light", "dark")

    def __init__(self):
        self.config = self.default()
        self.load()

    @staticmethod
    def default() -> ConfigParser:
        config = ConfigParser(allow_no_value=True)

        is_prod = getenv("APP.ENVIRONMENT", "production") == "production"

        config.add_section("app")
        config.set("app", "# 0-65535 (0 = random)")
        config.set("app", "port", "0" if is_prod else "49650")

        config.set("app", "# development / production")
        config.set("app", "environment", "production" if is_prod else "development")

        config.set("app", "# flask (single thread) / waitress")
        config.set("app", "server", "waitress" if is_prod else "flask")

        config.set("app", "# browser (will spawn only server and access will by through browser) / window")
        config.set("app", "mode", "window" if is_prod else "browser")

        config.add_section("settings")
        config.set("settings", "# 1.0 - X.X")
        config.set("settings", "scale", "1.0")

        config.set("settings", "# light / dark")
        config.set("settings", "theme", "dark")

        config.set("settings", "# en_US / ja_JP / ko_KR / zh_CN")
        config.set("settings", "language", "en_US")

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

    def __set_and_get(self, section: str, key: str, value=None):
        if value is not None:
            self.config.set(section, key, str(value))
            self.save()

        return self.config.get(section, key)

    def port(self, value: int = None) -> int:
        return int(self.__set_and_get("app", "port", value))

    def server(self, value: str = None) -> str:
        return self.__set_and_get("app", "server", value)

    def environment(self, value: str = None) -> str:
        return self.__set_and_get("app", "environment", value)

    def mode(self, value: str = None) -> str:
        return self.__set_and_get("app", "mode", value)

    def scale(self, value: float = None) -> float:
        return float(self.__set_and_get("settings", "scale", value))

    def theme(self, value: str = None) -> str:
        return self.__set_and_get("settings", "theme", value)

    def language(self, value: str = None) -> str:
        return self.__set_and_get("settings", "language", value)
