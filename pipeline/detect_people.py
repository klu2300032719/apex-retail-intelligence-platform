from ultralytics import YOLO

def load_detector():
    return YOLO("yolov8n.pt")
