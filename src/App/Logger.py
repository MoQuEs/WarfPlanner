from logging import StreamHandler, Formatter, getLogger, Logger, DEBUG
from sys import stderr
from flask import current_app

__setup = False
__logger_name = "app"
__level = DEBUG
__log_format = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
__logger = None


def _setup(logger_name: str = __logger_name, level: int = __level, log_format: str = __log_format) -> Logger:
    global __setup, __logger_name, __level, __log_format, __logger

    if __setup:
        return __logger

    __setup = True
    __logger_name = logger_name
    __level = level
    __log_format = log_format

    default_handler = StreamHandler(stderr)
    default_handler.setFormatter(Formatter(log_format))

    __logger = getLogger(logger_name)
    __logger.setLevel(level)
    __logger.addHandler(default_handler)

    return __logger


def get_logger() -> Logger:
    return current_app.logger if current_app else _setup()


def debug(msg, *args, **kwargs):
    get_logger().debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    get_logger().info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    get_logger().warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    get_logger().error(msg, *args, **kwargs)
