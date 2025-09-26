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
        "You are an AI food analyzer. Analyze the food in the provided image. "
        "Ignore humans, faces, hands, and personal information. Focus only on food and ingredients. "
        "Break down the dish into its visible and possible ingredients (e.g., for pizza: dough, cheese, tomato sauce, etc.). "
        "Return a JSON response with the dish name, ingredients (with name, estimated weight in grams, calories, allergens, macronutrients, and micronutrients), "
        "and total nutrition information for the dish. "
        "Respond strictly in JSON format, without explanations or markdown. "
        "Final JSON structure:\n"
        "{"
            "\"dish_name\": \"string\", "
            "\"ingredients\": [{"
                "\"name\": \"string\", "
                "\"weight_g\": number, "
                "\"calories_kcal\": number, "
                "\"allergens\": [\"string\", ...], "
                "\"macronutrients\": {...}, "
                "\"micronutrients\": {...}"
            "}], "
            "\"total\": {...}"
        "}"
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
