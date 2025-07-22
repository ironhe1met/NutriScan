# app/models/qwen_detector.py

import io, json
from pathlib import Path
from PIL import Image
import torch
from transformers import AutoProcessor, AutoModelForConditionalGeneration

class QwenFoodDetector:
    def __init__(self, model_dir: str):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # 1️⃣ Загружаем именно Qwen-специфичный Processor
        self.processor = AutoProcessor.from_pretrained(
            model_dir,
            trust_remote_code=True,   # очень важно!
            use_fast=True
        )
        # 2️⃣ Модель грузим лениво и с оптимизациями под большой объём
        self.model = AutoModelForConditionalGeneration.from_pretrained(
            model_dir,
            trust_remote_code=True,
            device_map="auto",
            low_cpu_mem_usage=True,
            torch_dtype="auto"
        )
        self.model.eval()

    def detect(self, image_path: str) -> dict:
        # 3️⃣ Открываем и конвертим картинку
        img = Image.open(Path(image_path)).convert("RGB")

        # 4️⃣ Ваш prompt — ОБЯЗАТЕЛЬНО с <image> токеном,
        #    он указывает где вставить визуальные фичи!
        prompt = (
            "<image> Detect foods and drinks in this image "
            "and output a JSON list of {\"bbox\": [x1,y1,x2,y2], \"label\": \"...\"}"
        )

        # 5️⃣ Формируем inputs: здесь processor сам создаст input_ids и pixel_values
        inputs = self.processor(
            images=img,
            text=prompt,
            return_tensors="pt"
        ).to(self.device)

        # 🔍 Для отладки можно раскомментировать:
        # print("input_ids:", inputs.input_ids.shape, "pixel_values:", inputs.pixel_values.shape)

        # 6️⃣ Генерим ответ
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False
        )

        # 7️⃣ Декодим и парсим JSON
        raw = self.processor.decode(outputs[0], skip_special_tokens=True)
        try:
            detections = json.loads(raw)
        except json.JSONDecodeError:
            detections = [{"error": raw}]
        return {"ingredients": detections}
