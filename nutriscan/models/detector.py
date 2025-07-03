from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
from ultralytics import YOLO

# Посилання на ваги моделі YOLO
WEIGHTS_URL = "https://github.com/ultralytics/assets/releases/download/v8.1.0/yolov8n-seg.pt"

class IngredientDetector:
    """Wrapper for YOLOv8 segmentation model."""

    def __init__(self, model_path: str | Path | None = None) -> None:
        self.model_path = Path(model_path or "weights/detector.pt")
        self.model: YOLO | None = None

    def load(self) -> None:
        """Loads YOLO model."""
        if self.model is None:
            if not self.model_path.exists():
                raise FileNotFoundError(
                    f"Weights not found at {self.model_path}. Run scripts/download_weights.py"
                )
            self.model = YOLO(str(self.model_path))

    def detect(self, image: Image.Image) -> list[dict[str, Any]]:
        """Returns list of detected ingredients with masks."""
        if self.model is None:
            raise RuntimeError("Model not loaded")
        if not isinstance(image, Image.Image):
            raise TypeError("Image must be a PIL.Image")
        results = self.model.predict(image, verbose=False)[0]
        detections: list[dict[str, Any]] = []
        names = self.model.names
        boxes = results.boxes
        masks = getattr(results, "masks", None)
        if boxes is None:
            return detections
        for i in range(len(boxes)):
            cls_id = int(boxes.cls[i].item())
            label = names.get(cls_id, str(cls_id)) if isinstance(names, dict) else names[cls_id]
            mask_arr = None
            area = 0.0
            if masks is not None:
                mask_arr = masks.data[i].cpu().numpy()
                area = float(mask_arr.sum())
            detections.append(
                {
                    "label": label,
                    "area": area,
                    "mask": mask_arr,
                }
            )
        return detections
