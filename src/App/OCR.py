import os
from threading import Thread

from .Image import Cords
from .Utils import easyocr_dir
from .Init import is_dev
from .Logger import get_logger

_started: bool = False
_language: list[str] = ["en"]
_easyocr_renderer = None
_setup_thread: Thread | None = None


def set_language(language: list[str]):
    global _language, _started

    if _language != language:
        _language = language
        _started = False


def _setup_easyocr():
    global _setup_thread, _started

    if _started:
        return

    def setup():
        global _easyocr_renderer, _language, _started
        import easyocr

        easyocr.easyocr.LOGGER = get_logger()

        _easyocr_renderer = easyocr.easyocr.Reader(
            _language, gpu=False, model_storage_directory=easyocr_dir(), verbose=is_dev
        )
        _started = True

    _setup_thread = Thread(target=setup)
    _setup_thread.start()


def _check_setup():
    global _started

    _setup_easyocr()
    _wait_for_setup()


def _wait_for_setup():
    global _setup_thread

    if _started:
        return

    if not _started and _setup_thread is not None:
        _setup_thread.join()
        _setup_thread = None


def from_local_image(image_path: str):
    _check_setup()

    if image_path is None or not os.path.exists(image_path):
        raise ValueError("Image path '%s' not found " % image_path)

    return _easyocr_renderer.readtext(image_path)


def from_image(image) -> list[tuple[Cords, str, float]]:
    _check_setup()

    return _easyocr_renderer.readtext(image)
