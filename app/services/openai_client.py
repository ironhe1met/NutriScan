import os
import base64
import json
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def analyze_image_base64(image_base64: str) -> dict:
    """Надіслати base64-зображення до GPT-4o та отримати відповідь у JSON."""
    if not openai.api_key:
        raise RuntimeError("❌ OPENAI_API_KEY is not set")

    if image_base64.startswith("data:image"):
        image_base64 = image_base64.split(",", 1)[1]

    system_prompt = (
        "Ти AI-нутриціолог. Проаналізуй їжу на зображенні. Визнач інгредієнти, приблизну вагу (в грамах), "
        "калорійність, білки, жири та вуглеводи для кожного. Поверни відповідь виключно у JSON-форматі "
        "такої структури без жодних коментарів, без крапок, без ```json, лише чистий JSON без переносу рядків: "
        '{"ingredients": [{"name": "...", "weight_g": ..., "calories_kcal": ..., "protein_g": ..., "fat_g": ..., "carbs_g": ...}], "total": {"calories_kcal": ..., "protein_g": ..., "fat_g": ..., "carbs_g": ...}}'
    )

    result = openai.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": system_prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
            }
        ],
        max_tokens=800
    )

    raw_text = result.choices[0].message.content

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        return {"raw_response": raw_text, "error": "❌ Не вдалося розпарсити JSON"}
