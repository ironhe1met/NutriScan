# app/models/qwen_detector.py

import io
import json
from pathlib import Path
from PIL import Image
import torch
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
from qwen_vl_utils import process_vision_info

class QwenFoodDetector:
    def __init__(self, model_dir: str):
        """
        Initialize the Qwen2.5-VL Food Detector.
        :param model_dir: Path to the directory containing the model files and configs.
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        # Load the processor with custom code support
        self.processor = AutoProcessor.from_pretrained(
            model_dir,
            trust_remote_code=True,
            use_fast=True
        )
        # Load the Qwen2.5-VL model optimized for CPU/GPU usage
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
        Detect foods and drinks in an image and return a JSON-like dict of detections.
        :param image_path: Path to the input image file.
        :return: Dict with key 'ingredients' mapping to a list of detections.
        Each detection is a dict with 'bbox' and 'label'.
        """
        # Open and convert image to RGB
        img = Image.open(Path(image_path)).convert("RGB")

        # Prepare the prompt with an <image> token
        prompt = (
            "<image> Detect foods and drinks in this image and output a JSON list "
            "of {\"bbox\": [x1,y1,x2,y2], \"label\": \"...\"}"
        )

        # Extract vision embeddings from the image
        vision_inputs, _ = process_vision_info([{"image": img}])

        # Build the model input text with embedded image markers
        chat_text = self.processor.apply_chat_template(
            [{"role": "user", "image": img, "text": prompt}],
            add_generation_prompt=True,
            tokenize=False
        )

        # Tokenize the combined text and vision inputs
        inputs = self.processor(
            text=[chat_text],
            images=vision_inputs,
            return_tensors="pt",
            padding=True
        ).to(self.device)

        # Generate the model output
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False
        )
        raw = self.processor.decode(outputs[0], skip_special_tokens=True)

        # Parse JSON or return error if invalid
        try:
            detections = json.loads(raw)
        except json.JSONDecodeError:
            detections = [{"error": raw}]
        return {"ingredients": detections}
