# app/models/qwen_detector.py

import json
from pathlib import Path
from PIL import Image
import torch
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
from qwen_vl_utils import process_vision_info

class QwenFoodDetector:
    def __init__(self, model_dir: str):
        """
        Initialize the Qwen2.5-VL food detector.
        :param model_dir: directory containing model and processor artifacts.
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Load multimodal processor (handles text+image)
        self.processor = AutoProcessor.from_pretrained(
            model_dir,
            trust_remote_code=True,
            use_fast=True
        )

        # Load Qwen2.5-VL model
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            model_dir,
            trust_remote_code=True,
            device_map="auto",
            low_cpu_mem_usage=True,
            torch_dtype="auto"
        )
        self.model.eval()

    def detect(self, image_path: str) -> dict:
        """
        Detect foods and drinks in an image and return ingredient detections.
        :param image_path: path to input image file
        :return: {'ingredients': [ {'bbox': [...], 'name': '...'}, ... ]}
        """
        # Load image
        img = Image.open(Path(image_path)).convert("RGB")

        # Prompt template with <image> marker
        prompt = (
            "<image> Detect foods and drinks in this image and output a JSON list "
            "of {\"bbox\": [x1,y1,x2,y2], \"label\": \"...\"}"
        )

        # Prepare conversation for vision processing
        conversation = [{"role": "user", "content": prompt, "image": img}]

        # Try using qwen_vl_utils to get fine-grained vision tokens
        try:
            vision_inputs, processed_conv = process_vision_info(conversation)
            # Fallback if processed_conv is None
            if not processed_conv:
                processed_conv = conversation
            # Extract content texts
            text_inputs = [msg.get("content", prompt) for msg in processed_conv]
            # Tokenize multimodal inputs
            inputs = self.processor(
                text=text_inputs,
                images=vision_inputs,
                return_tensors="pt",
                padding=True
            )
        except Exception:
            # Fallback: use AutoProcessor directly on image+text
            inputs = self.processor(
                text=[prompt],
                images=img,
                return_tensors="pt",
                padding=True
            )

        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate output
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False
        )

        # Decode and parse
        raw = self.processor.decode(outputs[0], skip_special_tokens=True)
        try:
            detections = json.loads(raw)
        except json.JSONDecodeError:
            detections = [{"error": raw}]

        # Normalize key 'label' to 'name'
        for det in detections:
            if "label" in det and "name" not in det:
                det["name"] = det.pop("label")
        return {"ingredients": detections}
