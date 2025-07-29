import os
import json
import urllib.request

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"


def analyze_image_base64(image_base64: str) -> dict:
    """Send a base64 image to OpenAI Vision and return raw text response."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe the food in this image"},
                    {"type": "image_url", "image_url": {"url": image_base64}},
                ],
            }
        ],
        "max_tokens": 200,
    }

    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        OPENAI_API_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req) as resp:
        resp_data = json.load(resp)

    raw_text = resp_data["choices"][0]["message"]["content"]
    return {"raw_response": raw_text}
