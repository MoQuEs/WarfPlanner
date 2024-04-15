from typing import NamedTuple, Any

_started: bool = False
_adb = None

ak_app = {
    "com.hypergryph.arknights": ("ch_sim", "zh_CN", False, True),
    "com.YoStarEN.Arknights": ("en", "en_US", True, False),
    "com.YoStarJP.Arknights": ("ja", "ja_JP", True, False),
    "com.YoStarKR.Arknights": ("ko", "ko_KR", True, False),
}


class Device(NamedTuple):
    device: Any
    ocr_language: str
    app_language: str
    is_global: bool
    is_cn: bool


def setup_adb():
    global _adb, _started

    if _started:
        return _adb

    def setup():
        global _adb, _started
        from adbutils import adb

        _adb = adb
        _started = True

        return _adb

    return setup()


def get_devices_with_ak() -> list[Device]:
    devices = []

    for device in setup_adb().device_list():
        app_info = device.app_current()
        if app_info.package in ak_app:
            devices.append(
                Device(
                    device,
                    ak_app[app_info.package][0],
                    ak_app[app_info.package][1],
                    ak_app[app_info.package][2],
                    ak_app[app_info.package][3],
                )
            )

    return devices


def screenshot(device) -> bytes:
    setup_adb()

    image_stream = device.shell(["screencap", "-p"], stream=True)
    return image_stream.read_until_close(None)
