# app/models/qwen_detector.py

import json
from pathlib import Path
from PIL import Image
import torch
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration

class QwenFoodDetector:
    def __init__(self, model_dir: str):
        """
        Initialize the Qwen2.5-VL multimodal detector.
        :param model_dir: Directory containing model and processor files.
        """
        # choose device
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

        # load processor and model
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
        # load image
        img = Image.open(Path(image_path)).convert("RGB")
        # define prompt
        prompt = (
            'Detect foods and drinks in this image and return a JSON list '
            'of {"bbox": [x1,y1,x2,y2], "label": "..."}'
        )
        # process vision: inject image tokens and prepare image features
        vision_inputs, processed_conversation = process_vision_info([
            {"image": img, "content": prompt}
        ])
        # extract text inputs with <image> markers from processed conversation
        text_inputs = [msg["content"] for msg in processed_conversation]
        # tokenize multimodal inputs
        inputs = self.processor(
            text=text_inputs,
            images=vision_inputs,
            return_tensors="pt",
            padding=True
        )
        # move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        # generate outputs
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False
        )
        # decode to string
        raw = self.processor.decode(outputs[0], skip_special_tokens=True)
        # parse JSON
        try:
            detections = json.loads(raw)
        except json.JSONDecodeError:
            detections = [{"error": raw}]
        # normalize label->name
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
        # build text conversation
        conversation = [{"role": "user", "text": text}]
        # tokenize conversation
        inputs = self.processor(
            conversation,
            return_tensors="pt",
            padding=True
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        # generate
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False
        )
        # decode and return
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
