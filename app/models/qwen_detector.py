# app/models/qwen_detector.py

import io
import json
from pathlib import Path
from PIL import Image
import torch
from transformers import AutoProcessor
# для старіших версій transformers fallback на AutoModelForSeq2SeqLM
try:
    from transformers import AutoModelForConditionalGeneration
except ImportError:
    from transformers import AutoModelForSeq2SeqLM as AutoModelForConditionalGeneration
from qwen_vl_utils import process_vision_info   # ← новий імпорт

class QwenFoodDetector:
    def __init__(self, model_dir: str):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # завантажуємо processor з trust_remote_code=True
        self.processor = AutoProcessor.from_pretrained(
            model_dir,
            trust_remote_code=True,
            use_fast=True
        )
        self.model = AutoModelForConditionalGeneration.from_pretrained(
            model_dir,
            trust_remote_code=True,
            device_map="auto",
            low_cpu_mem_usage=True,
            torch_dtype="auto"
        )
        self.model.eval()

    def detect(self, image_path: str) -> dict:
        img = Image.open(Path(image_path)).convert("RGB")

        # 1) Формуємо “повідомлення” для chat-шаблону
        prompt = "Detect foods and drinks in this image and output a JSON list of {\"bbox\": [x1,y1,x2,y2], \"label\": \"...\"}"

        # 2) Підготовка векторів картинки
        # process_vision_info повертає дві структури — images & videos
        vision_inputs, _ = process_vision_info([{"image": img}])

        # 3) Формуємо текст за допомогою ChatTemplate
        # метод apply_chat_template вмонтує в текст маркери для візуальної частини
        text = self.processor.apply_chat_template(
            [{"role": "user", "image": img, "text": prompt}],
            add_generation_prompt=True,
            tokenize=False
        )

        # 4) Токенізуємо вже готовий текст + підставляємо картинки
        inputs = self.processor(
            text=[text],
            images=vision_inputs,
            return_tensors="pt",
            padding=True
        ).to(self.device)

        # 5) Генеруємо відповідь
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
