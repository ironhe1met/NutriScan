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
        Qwen2.5-VL based food detector initialization.
        :param model_dir: directory path where model artifacts are stored.
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # Load the custom processor that handles image + text inputs
        self.processor = AutoProcessor.from_pretrained(
            model_dir,
            trust_remote_code=True,
            use_fast=True
        )
        # Load the Qwen2.5-VL model for conditional generation
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            model_dir,
            trust_remote_code=True,
            device_map="auto",
            low_cpu_mem_usage=True,
            torch_dtype="auto"
        )
        # Apply dynamic quantization to reduce memory and speed up inference on CPU
        self.model = torch.quantization.quantize_dynamic(
            self.model,
            {torch.nn.Linear},
            dtype=torch.qint8
        )
        self.model.eval()

    def detect(self, image_path: str) -> dict:
        """
        Detect foods and drinks in the image located at image_path.
        Returns a dict: {'ingredients': [ { 'bbox': [...], 'name': '...' }, ... ] }
        """
        # Load and convert image
        img = Image.open(Path(image_path)).convert("RGB")

        # Define the prompt with the <image> token placeholder
        prompt = (
            "<image> Detect foods and drinks in this image and output a JSON list "
            "of {\"bbox\": [x1,y1,x2,y2], \"label\": \"...\"}"
        )

        # Build the conversation list with 'content' key for qwen_vl_utils
        conversation = [
            {"role": "user", "content": prompt, "image": img}
        ]

        # Process vision information and get updated conversation
        vision_inputs, processed_conversation = process_vision_info(conversation)

        # Build text inputs list, handling both possible keys
        text_inputs = [msg.get("text") or msg.get("content") for msg in processed_conversation or []]
        if not text_inputs:
            # fallback to single prompt if processing failed
            text_inputs = [prompt]

        # Tokenize text+vision inputs together
        inputs = self.processor(
            text=text_inputs,
            images=vision_inputs,
            return_tensors="pt",
            padding=True
        ).to(self.device)

        # Generate model output
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False
        )

        # Decode to string and parse JSON
        raw = self.processor.decode(outputs[0], skip_special_tokens=True)
        try:
            detections = json.loads(raw)
        except json.JSONDecodeError:
            detections = [{"error": raw}]
        # Remap label key to name for NutritionService compatibility
        for det in detections:
            if "label" in det and "name" not in det:
                det["name"] = det.pop("label")
        return {"ingredients": detections}
