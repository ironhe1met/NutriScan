from ultralytics import YOLO
import torch
import cv2

class IngredientDetector:
    def __init__(self, model_path="models/yolov8x-seg.pt"):
        self.model = YOLO(model_path)

    def detect(self, image_path):
        results = self.model(image_path, conf=0.25)[0]
        ingredients = []

        for box in results.boxes:
            cls_id = int(box.cls.item())
            name = results.names[cls_id]
            conf = round(box.conf.item(), 4)
            ingredients.append({"name": name, "confidence": conf})

        return {"ingredients": ingredients}



        