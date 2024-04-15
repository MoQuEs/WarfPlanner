import os
from threading import Thread
from typing import Any

from .Image import Cords, Image
from .Utils import easyocr_dir
from .Init import is_dev
from .Logger import get_logger

_started: dict[str, bool] = {}
_easyocr_renderer: dict[str, Any] = {}
_setup_threads: dict[str, Thread | None] = {}


def _lang_key(languages: list[str]) -> str:
    return "".join(sorted(set(languages)))


def setup_easyocr(languages: list[str] = ["en"]):
    global _setup_threads, _started

    lang_index = _lang_key(languages)

    if lang_index in _started and _started[lang_index]:
        return

    def setup():
        global _easyocr_renderer, _started
        import easyocr

        easyocr.easyocr.LOGGER = get_logger()

        _easyocr_renderer[lang_index] = easyocr.easyocr.Reader(
            languages, model_storage_directory=easyocr_dir(), verbose=is_dev
        )

        _started[lang_index] = True

    _setup_threads[lang_index] = Thread(target=setup)
    _setup_threads[lang_index].start()


def _check_setup(languages: list[str] = ["en"]):
    global _started

    setup_easyocr(languages)
    _wait_for_setup(languages)


def _wait_for_setup(languages: list[str] = ["en"]):
    global _setup_threads

    lang_index = _lang_key(languages)

    if lang_index in _started and _started[lang_index]:
        return

    if lang_index in _setup_threads:
        _setup_threads[lang_index].join()
        _setup_threads[lang_index] = None


def from_local_image(image_path: str, languages: list[str] = ["en"]) -> list[tuple[Cords, str, float]]:
    _check_setup(languages)

    if image_path is None or not os.path.exists(image_path):
        raise ValueError("Image path '%s' not found " % image_path)

    return _easyocr_renderer[_lang_key(languages)].readtext(image_path)


def from_image(image: Image | bytes, languages: list[str] = ["en"]) -> list[tuple[Cords, str, float]]:
    _check_setup(languages)

    return _easyocr_renderer[_lang_key(languages)].readtext(image)
