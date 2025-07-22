import io, json
from PIL import Image
import torch
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

class QwenFoodDetector:
    def __init__(self, model_dir: str):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.processor = AutoProcessor.from_pretrained(model_dir, trust_remote_code=False)
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(model_dir, trust_remote_code=False).to(self.device)
        self.model.eval()

    def detect(self, image_path: str) -> dict:
        img = Image.open(image_path).convert("RGB")

        # ↓ Ось тут вставляємо маркер <image> перед текстом
        prompt = (
            "<image> Detect foods and drinks in this image and "
            "output a JSON list of {\"bbox\": [x1,y1,x2,y2], \"label\": \"…\"}"
        )

        inputs = self.processor(
            images=img,
            text=prompt,
            return_tensors="pt"
        ).to(self.device)

        outputs = self.model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False
        )
        raw = self.processor.decode(outputs[0], skip_special_tokens=True)
        try:
            detections = json.loads(raw)
        except json.JSONDecodeError:
            detections = [{"error": raw}]
        return {"ingredients": detections}