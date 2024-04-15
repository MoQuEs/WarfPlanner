import adbutils


class AdbDevice(adbutils.AdbDevice):
    def __screencap(self) -> bytes:
        image_stream = self.shell(["screencap", "-p"], stream=True)
        return image_stream.read_until_close(None)

    def screenshot(self) -> bytes:
        return self.__screencap()
