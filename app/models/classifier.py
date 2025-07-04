import torch
from torchvision import transforms, models
from PIL import Image
import json

MODEL_PATH = "models/classifier.pth"
LABELS_PATH = "app/assets/labels_food101.json"

class FoodClassifier:
    def __init__(self):
        self.model = models.efficientnet_b0(weights=None)
        self.model.classifier[1] = torch.nn.Linear(self.model.classifier[1].in_features, 101)

        state_dict = torch.load(MODEL_PATH, map_location="cpu")
        self.model.load_state_dict(state_dict)
        self.model.eval()

        with open(LABELS_PATH, "r") as f:
            self.id2label = json.load(f)  # <== оновлено

        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                 std=[0.229, 0.224, 0.225])
        ])

    def predict(self, image_path: str):
        img = Image.open(image_path).convert("RGB")
        img_tensor = self.transform(img).unsqueeze(0)

        with torch.no_grad():
            outputs = self.model(img_tensor)
            probs = torch.nn.functional.softmax(outputs[0], dim=0)
            confidence, predicted_idx = torch.max(probs, 0)

            return {
                "dish_name": self.id2label[str(predicted_idx.item())],  # <== оновлено
                "confidence": round(confidence.item(), 4)
            }
