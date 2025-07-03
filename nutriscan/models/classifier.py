from pathlib import Path
from typing import Sequence

import torch
from torchvision import models, transforms
from PIL import Image

# Пряме посилання на файл з вагами моделі (EfficientNet-B0)
# У репозиторії HuggingFace файл називається `weights.pt`
MODEL_URL = "https://huggingface.co/dwililiya/food101-model-classification/resolve/main/weights.pt"

class FoodClassifier:
    """Wrapper for food classification model."""

    def __init__(self, model_path: str | Path | None = None) -> None:
        self.model_path = Path(model_path or "weights/classifier.pt")
        self.model: torch.nn.Module | None = None
        self.classes: Sequence[str] | None = None
        self.transform = transforms.Compose(
            [
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
                ),
            ]
        )

    def load(self) -> None:
        """Loads the model from a local path or downloads it."""
        if self.model is None:
            model = models.efficientnet_b0(num_classes=101)
            if self.model_path.exists():
                state = torch.load(self.model_path, map_location="cpu")
                if isinstance(state, dict):
                    weights = (
                        state.get("model_state_dict")
                        or state.get("state_dict")
                        or state.get("model")
                        or state
                    )
                    classes = (
                        state.get("classes")
                        or state.get("class_names")
                        or state.get("idx_to_class")
                    )
                    if classes:
                        if isinstance(classes, dict):
                            classes = [
                                cls for _, cls in sorted(classes.items(), key=lambda x: int(x[0]))
                            ]
                        self.classes = list(classes)
                else:
                    weights = state
                model.load_state_dict(weights)
            else:
                raise FileNotFoundError(
                    f"Weights not found at {self.model_path}. Run scripts/download_weights.py"
                )
            model.eval()
            self.model = model

    def predict(self, image) -> str:
        """Returns predicted label for the image."""
        if self.model is None:
            raise RuntimeError("Model not loaded")
        if not isinstance(image, Image.Image):
            raise TypeError("Image must be a PIL.Image")
        with torch.no_grad():
            inp = self.transform(image).unsqueeze(0)
            logits = self.model(inp)
            idx = int(logits.argmax(dim=1).item())
        if self.classes and idx < len(self.classes):
            return self.classes[idx]
        return str(idx)
