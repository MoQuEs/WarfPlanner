from pprint import pprint
from App.Image import pill__to__cv2, XYXY
from App.OCR import from_image


def main() -> None:
    from adbutils import adb

    devices = adb.device_list()
    for device in devices:
        print(device.prop.name, device.prop.model, device.prop.device)
        print(device.get_serialno(), device.get_devpath(), device.get_state(), device.get_state())
        app_info = device.app_current()
        print(device.serial, app_info.package, app_info.activity, app_info.pid)

        {
            "com.hypergryph.arknights": "ch_sim",
            "com.YoStarEN.Arknights": "en",
            "com.YoStarKR.Arknights": "ko",
            "com.YoStarJP.Arknights": "ja",
        }

    device = adb.device()
    app_info = device.app_current()
    pprint([app_info.package, app_info.activity, app_info.pid])

    pil_img = device.screenshot()

    result = from_image(pill__to__cv2(pil_img))
    for line in result:
        if line[1] == "Sniper":
            device.click(*XYXY.from_cords(line[0]).center())


if __name__ == "__main__":
    main()
