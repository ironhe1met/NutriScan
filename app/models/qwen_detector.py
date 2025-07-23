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
        Initialize the Qwen2.5-VL multimodal detector.
        :param model_dir: Directory containing model and processor files.
        """
        # Choose device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Load processor and model
        self.processor = AutoProcessor.from_pretrained(
            model_dir,
            trust_remote_code=True,
            use_fast=True
        )
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            model_dir,
            trust_remote_code=True,
            device_map="auto",
            low_cpu_mem_usage=True,
            torch_dtype="auto"
        ).to(self.device)
        self.model.eval()

    def detect(self, image_path: str) -> dict:
        """
        Detect foods and drinks in an image and return structured JSON.
        :param image_path: Path to the input image file.
        :return: {'ingredients': [ {'bbox': [...], 'name': '...'}, ... ]}
        """
        # Load image
        img = Image.open(Path(image_path)).convert("RGB")

        # Define prompt with <image> placeholder
        prompt = (
            '<image> Detect foods and drinks in this image and return a JSON list '
            'of {"bbox": [x1,y1,x2,y2], "label": "..."}'
        )

        # Process vision: obtain image features and aligned text tokens
        vision_inputs, processed_conv = process_vision_info([
            {"role": "user", "content": prompt, "image": img}
        ])
        if not processed_conv:
            processed_conv = [{"content": prompt}]
        # Extract text inputs from processed conversation
        text_inputs = [msg.get("content", prompt) for msg in processed_conv]

        # Tokenize multimodal inputs
        inputs = self.processor(
            text=text_inputs,
            images=vision_inputs,
            return_tensors="pt",
            padding=True
        )
        # Move tensors to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate outputs
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False
        )

        # Decode to string
        raw = self.processor.decode(outputs[0], skip_special_tokens=True)

        # Parse JSON or return error
        try:
            detections = json.loads(raw)
        except json.JSONDecodeError:
            detections = [{"error": raw}]

        # Normalize key 'label' -> 'name'
        for det in detections:
            if "label" in det and "name" not in det:
                det["name"] = det.pop("label")

        return {"ingredients": detections}

    def query(self, text: str, max_new_tokens: int = 128) -> str:
        """
        Send a text-only query to the model for testing text capability.
        :param text: Input text prompt.
        :param max_new_tokens: Maximum tokens to generate.
        :return: Generated response string.
        """
        # Build text-only conversation
        conversation = [{"role": "user", "content": text}]

        # Tokenize conversation
        inputs = self.processor(
            conversation,
            return_tensors="pt",
            padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False
        )

        # Decode and return
        return self.processor.decode(outputs[0], skip_special_tokens=True)


if __name__ == "__main__":
    import argparse, json
    parser = argparse.ArgumentParser(description="Qwen2.5-VL CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--image", type=str, help="Path to image file")
    group.add_argument("--text", type=str, help="Text prompt for the model")
    parser.add_argument(
        "--model_dir", type=str,
        default="models/qwen2.5-vl-7b-instruct",
        help="Directory containing Qwen model"
    )
    args = parser.parse_args()
    detector = QwenFoodDetector(args.model_dir)
    if args.image:
        result = detector.detect(args.image)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(detector.query(args.text))
