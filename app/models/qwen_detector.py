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
        Initialize Qwen2.5-VL Food Detect model from local files.
        :param model_dir: Local directory containing the fine-tuned Food Detect model.
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # Load processor and model from local files only
        self.processor = AutoProcessor.from_pretrained(
            model_dir,
            trust_remote_code=True,
            use_fast=True,
            local_files_only=True
        )
        self.model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            model_dir,
            trust_remote_code=True,
            device_map="auto",
            low_cpu_mem_usage=True,
            torch_dtype="auto",
            local_files_only=True
        ).to(self.device)
        self.model.eval()

    def detect(self, image_path: str) -> dict:
        """
        Detect foods and drinks in an image and return structured JSON.
        :param image_path: Path to the input image file.
        :return: {'ingredients': [ {'bbox': [...], 'name': '...'}, ... ]}
        """
        img = Image.open(Path(image_path)).convert("RGB")
        prompt = (
            '<image> Detect foods and drinks in this image and return '
            'a JSON list of {"bbox": [x1,y1,x2,y2], "label": "..."}'
        )

        # Process vision: get embeddings and aligned prompt
        vision_inputs, processed_conv = process_vision_info([
            {"role": "user", "content": prompt, "image": img}
        ])
        # Fallback if processing returns None
        if processed_conv is None:
            processed_conv = [{"content": prompt}]
        text_inputs = [msg.get("content", prompt) for msg in processed_conv]

        # Tokenize multimodal inputs locally
        inputs = self.processor(
            text=text_inputs,
            images=vision_inputs,
            return_tensors="pt",
            padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

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

        for det in detections:
            if "label" in det and "name" not in det:
                det["name"] = det.pop("label")

        return {"ingredients": detections}

    def query(self, text: str, max_new_tokens: int = 128) -> str:
        """
        Text-only query for descriptions, calories, etc.
        """
        inputs = self.processor(
            text=[text],
            return_tensors="pt",
            padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False
        )
        return self.processor.decode(outputs[0], skip_special_tokens=True)

if __name__ == "__main__":
    import argparse, json
    parser = argparse.ArgumentParser(description="Qwen2.5-VL Food Detect CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--image", type=str, help="Path to image file for detection")
    group.add_argument("--text", type=str, help="Text prompt for text-only query")
    parser.add_argument(
        "--model_dir", type=str,
        default="models/qwen2.5-vl-food-detect",
        help="Local directory of the Food Detect model"
    )
    args = parser.parse_args()
    detector = QwenFoodDetector(args.model_dir)
    if args.image:
        result = detector.detect(args.image)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(detector.query(args.text))
