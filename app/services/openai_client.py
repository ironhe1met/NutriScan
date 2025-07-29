import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


def analyze_image_base64(image_base64: str) -> dict:
    """Надіслати зображення (base64) до GPT-4 Vision та отримати відповідь."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("❌ OPENAI_API_KEY is not set in environment")

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Опиши інгредієнти страви з вагою (грам), калоріями та БЖУ."},
                    {"type": "image_url", "image_url": {"url": image_base64}},
                ],
            }
        ],
        "max_tokens": 500,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    response = requests.post(OPENAI_API_URL, headers=headers, json=payload)
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]
    return {"raw_response": content}
