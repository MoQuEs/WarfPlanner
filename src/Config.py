import configparser

from Utils import src_dir


class Config:
    config: configparser.ConfigParser
    app_mode_default = "window"
    app_modes = ("window", "browser")
    app_environments = ("production", "development")
    settings_modes = ("light", "dark")

    def __init__(self):
        self.config = configparser.ConfigParser()
        self.load()

    def load(self):
        self.config.read(src_dir("App.ini"))

    def save(self):
        with open(src_dir("App.ini"), "w") as file:
            self.config.write(file)

    def __set_and_get(self, section: str, key: str, value=None):
        if value is not None:
            self.config.set(section, key, str(value))
            self.save()

        return self.config.get(section, key)

    def port(self, value: int = None) -> int:
        return int(self.__set_and_get("app", "port", value))

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
