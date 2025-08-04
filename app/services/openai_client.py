import os
import base64
import json
import re
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def extract_json_from_text(text: str) -> str:
    """Спробувати витягнути JSON із тексту, навіть якщо він в ```json ...```"""
    # Якщо модель повертає обгорнутий формат
    match = re.search(r'```json\s*({.*?})\s*```', text, re.DOTALL)
    if match:
        return match.group(1)

    # Якщо просто є JSON у тілі
    match = re.search(r'({.*})', text, re.DOTALL)
    if match:
        return match.group(1)

    return text  # fallback

def analyze_image_base64(image_base64: str) -> dict:
    """Надіслати base64-зображення до GPT-4o та отримати JSON-відповідь."""
    if not openai.api_key:
        raise RuntimeError("❌ OPENAI_API_KEY is not set")

    if image_base64.startswith("data:image"):
        image_base64 = image_base64.split(",", 1)[1]

    system_prompt = (
        "You are an AI nutritionist. Analyze the food in the image. "
        "Identify ingredients, estimate their weight (in grams), and provide calories, protein, fat, and carbs for each. "
        "Respond strictly in JSON format only, without any explanations, comments, markdown, or code blocks. "
        "The JSON must follow this structure and contain only English keys and values:\n"
        '{"ingredients": [{"name": "...", "weight_g": ..., "calories_kcal": ..., "protein_g": ..., "fat_g": ..., "carbs_g": ...}], '
        '"total": {"calories_kcal": ..., "protein_g": ..., "fat_g": ..., "carbs_g": ...}}'
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
    extracted_json = extract_json_from_text(raw_text)

    try:
        return json.loads(extracted_json)
    except json.JSONDecodeError:
        return {"raw_response": raw_text, "error": "❌ Не вдалося розпарсити JSON"}
