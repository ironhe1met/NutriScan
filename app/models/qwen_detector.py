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
        :param model_dir: Path to the directory containing model files.
        """
        # Determine device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Load processor with custom code support
        self.processor = AutoProcessor.from_pretrained(
            model_dir,
            trust_remote_code=True,
            use_fast=True
        )

        # Load Qwen2.5-VL model optimized for CPU/GPU
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
        Run detection on the given image and return ingredients list.
        :param image_path: Local path to the image file.
        :return: Dict with key 'ingredients' mapping to list of detections.
                 Each detection has 'bbox' and 'name'.
        """
        # Load and prepare image
        img = Image.open(Path(image_path)).convert("RGB")

        # Define prompt for model, using <image> placeholder
        prompt = (
            "<image> Detect foods and drinks in this image and output a JSON list "
            "of {\"bbox\": [x1,y1,x2,y2], \"label\": \"...\"}"
        )

        # Build conversation for vision processing
        conversation = [{
            "role": "user",
            "content": prompt,
            "image": img
        }]

        # Process vision info and augment conversation
        vision_inputs, processed_conversation = process_vision_info(conversation)

        # Extract text messages from processed conversation
        text_inputs = [msg["content"] for msg in processed_conversation]

        # Tokenize text + vision inputs
        inputs = self.processor(
            text=text_inputs,
            images=vision_inputs,
            return_tensors="pt",
            padding=True
        ).to(self.device)

        # Perform generation
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False
        )

        # Decode output and parse JSON
        raw = self.processor.decode(outputs[0], skip_special_tokens=True)
        try:
            detections = json.loads(raw)
        except json.JSONDecodeError:
            detections = [{"error": raw}]

        # Rename 'label' to 'name' for compatibility
        for det in detections:
            if "label" in det and "name" not in det:
                det["name"] = det.pop("label")

        return {"ingredients": detections}
