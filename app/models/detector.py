from ultralytics import YOLO
import torch
import cv2

class IngredientDetector:
    def __init__(self, model_path="models/yolov8x-seg.pt", weight_scaling_factor=0.05):
        self.model = YOLO(model_path)
        self.weight_scaling_factor = weight_scaling_factor  # коефіцієнт для розрахунку ваги

    def detect(self, image_path):
        results = self.model(image_path, conf=0.25)[0]
        ingredients = []

        for box, mask in zip(results.boxes, results.masks.data):
            cls_id = int(box.cls.item())
            name = results.names[cls_id]
            conf = round(box.conf.item(), 4)

            # Обчислюємо площу маски (кількість пікселів == 1)
            mask_area = torch.sum(mask).item()

            # Оцінюємо вагу з урахуванням масштабу
            weight_g = int(mask_area * self.weight_scaling_factor)

            ingredients.append({
                "name": name,
                "confidence": conf,
                "weight_g": weight_g
            })

        return {"ingredients": ingredients}
