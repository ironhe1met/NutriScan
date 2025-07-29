import os
import base64
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


def analyze_image_base64(image_base64: str) -> dict:
    """Надіслати base64-зображення до GPT-4o через OpenAI SDK."""
    if not openai.api_key:
        raise RuntimeError("❌ OPENAI_API_KEY is not set")

    # Видалити префікс, якщо є
    if image_base64.startswith("data:image"):
        image_base64 = image_base64.split(",", 1)[1]

    result = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Опиши інгредієнти страви з вагою (грам), калоріями та БЖУ."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}},
                ],
            }
        ],
        max_tokens=500
    )

    content = result.choices[0].message.content
    return {"raw_response": content}
