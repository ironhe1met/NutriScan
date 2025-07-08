from ultralytics import YOLO
import numpy as np

class IngredientDetector:
    def __init__(self, model_path="models/yolov8x-seg.pt"):
        self.model = YOLO(model_path)

    def estimate_weight(self, mask: np.ndarray) -> int:
        area = np.sum(mask == 1)
        weight = int(area * 0.05)  # коефіцієнт підібрано емпірично
        return max(weight, 1)

    def detect(self, image_path):
        results = self.model(image_path, conf=0.25)[0]
        ingredients = []

        for i, mask in enumerate(results.masks.data):
            cls_id = int(results.boxes.cls[i].item())
            name = results.names[cls_id]
            conf = round(results.boxes.conf[i].item(), 4)
            mask_np = mask.cpu().numpy()
            weight = self.estimate_weight(mask_np)

            ingredients.append({
                "name": name,
                "confidence": conf,
                "weight_g": weight
            })

        return {"ingredients": ingredients}
