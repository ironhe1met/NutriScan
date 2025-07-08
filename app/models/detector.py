import cv2
import numpy as np

# всередині класу IngredientDetector
def estimate_weight(self, mask: np.ndarray) -> int:
    """
    Оцінити вагу в грамах на основі площі маски.
    """
    area = np.sum(mask == 1)
    # коефіцієнт масштабування (підбирається емпірично, напр. 0.05 г за 1 піксель)
    weight = int(area * 0.05)
    return max(weight, 1)

def detect(self, image_path: str) -> list:
    results = self.model(image_path)
    ingredients = []

    for result in results:
        names = result.names
        for i, seg in enumerate(result.masks.data):
            cls_id = int(result.boxes.cls[i].item())
            name = names[cls_id]
            conf = float(result.boxes.conf[i].item())
            mask = seg.cpu().numpy()
            weight = self.estimate_weight(mask)

            ingredients.append({
                "name": name,
                "confidence": round(conf, 4),
                "weight_g": weight
            })

    return ingredients
