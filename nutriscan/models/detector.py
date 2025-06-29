from pathlib import Path

# Посилання на ваги моделі YOLO
WEIGHTS_URL = "https://github.com/ultralytics/assets/releases/download/v8.1.0/yolov8n-seg.pt"

class IngredientDetector:
    """Wrapper for YOLOv8 segmentation model."""

    def __init__(self, model_path: str | Path | None = None) -> None:
        self.model_path = Path(model_path) if model_path else None
        self.model = None

    def load(self) -> None:
        """Loads YOLO model."""
        if self.model is None:
            # Placeholder for actual YOLO model loading
            self.model = object()

    def detect(self, image):
        """Returns list of detected ingredients with masks."""
        if self.model is None:
            raise RuntimeError("Model not loaded")
        # Placeholder: return empty list
        return []
