from ultralytics import yolov8


class AI:
    def __init__(self):
        torch.hub.load("ultralytics/yolov5", "yolov5s", pretrained=True)

    def get_move(self, board):
        pass
