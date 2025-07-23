# app/models/qwen_detector.py

import json
from pathlib import Path
from PIL import Image
import torch
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

class QwenFoodDetector:
    def __init__(self, model_dir: str):
        """
        Initialize the Qwen2.5-VL food detector and text query model.
        :param model_dir: Path to the directory containing model artifacts.
        """
        # Choose device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Load processor that supports multimodal inputs
        self.processor = AutoProcessor.from_pretrained(
            model_dir,
            trust_remote_code=True,
            use_fast=True
        )

        # Load the multimodal Qwen model
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
        :param image_path: Local path to the image file.
        :return: Dict with key 'ingredients' mapping to a list of detections
                 where each detection has 'bbox' and 'name'.
        """
        # Load and prepare image
        img = Image.open(Path(image_path)).convert("RGB")

        # Prompt for detection; include <image> token placeholder
        prompt = (
            "<image> Detect foods and drinks in this image and "
            "return a JSON list of {\\"bbox\\": [x1,y1,x2,y2], \\\"label\\\": \\\"...\\\"}"
        )

        # Build conversation with image and text
        conversation = [{"role": "user", "text": prompt, "image": img}]

        # Tokenize multimodal conversation
        inputs = self.processor(
            conversation,
            return_tensors="pt",
            padding=True
        )
        # Move inputs to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate output tokens
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False
        )

        # Decode and parse JSON
        raw = self.processor.decode(outputs[0], skip_special_tokens=True)
        try:
            detections = json.loads(raw)
        except json.JSONDecodeError:
            detections = [{"error": raw}]

        # Rename 'label' to 'name' for NutritionService
        for det in detections:
            if "label" in det and "name" not in det:
                det["name"] = det.pop("label")
        return {"ingredients": detections}

    def query(self, text: str, max_new_tokens: int = 128) -> str:
        """
        Send a text-only query to the model for testing text capability.
        :param text: The input text prompt.
        :param max_new_tokens: Maximum tokens to generate.
        :return: Generated text response from the model.
        """
        # Build text-only conversation
        conversation = [{"role": "user", "text": text}]

        # Tokenize text conversation
        inputs = self.processor(
            conversation,
            return_tensors="pt",
            padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate response
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False
        )
        # Decode and return
        return self.processor.decode(outputs[0], skip_special_tokens=True)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Qwen2.5-VL Food Detector & Text Query CLI"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--image", type=str,
        help="Path to image file for detection"
    )
    group.add_argument(
        "--text", type=str,
        help="Text prompt for text-only query"
    )
    parser.add_argument(
        "--model_dir", type=str,
        default="models/qwen2.5-vl-7b-instruct",
        help="Directory of Qwen2.5-VL model files"
    )
    args = parser.parse_args()

    detector = QwenFoodDetector(args.model_dir)
    if args.image:
        result = detector.detect(args.image)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        response = detector.query(args.text)
        print(response)
