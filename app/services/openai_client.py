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
        "You are an AI food analyzer. Analyze the food in the image. "
        "Ignore humans, faces, hands, and any personal information. "
        "Focus only on food and ingredients. "
        "You must always break down the dish into its visible and possible ingredients, not only provide a single total. "
        "For example, if the dish is pizza, decompose it into dough, cheese, tomato sauce, vegetables, meat, etc. "
        "Identify the dish name, list all ingredients with their estimated weight (in grams), and provide detailed nutrition information. "
        "For each ingredient include calories, allergens (if any), a full set of macronutrients, and available micronutrients. "
        "Also calculate totals for the whole dish in the same structure. "
        "Respond strictly in JSON format only, without any explanations, comments, markdown, or code blocks. "
        "If a nutrient or value is not available, omit the field completely (do not return empty objects or arrays). "
        "All keys and values must be in English. "
        "Final JSON structure:\n"
        '{'
            '"dish_name": "string", '
            '"ingredients": ['
                '{'
                    '"name": "string", '
                    '"weight_g": number, '
                    '"calories_kcal": number, '
                    '"allergens": ["string", ...], '
                    '"macronutrients": {'
                        '"protein_g": number, '
                        '"fat_g": number, '
                        '"saturated_fat_g": number, '
                        '"trans_fat_g": number, '
                        '"monounsaturated_fat_g": number, '
                        '"polyunsaturated_fat_g": number, '
                        '"carbs_g": number, '
                        '"fiber_g": number, '
                        '"sugars_g": number, '
                        '"starch_g": number, '
                        '"cholesterol_mg": number, '
                        '"water_g": number'
                    '}, '
                    '"micronutrients": {'
                        '"vitamins": {'
                            '"vitamin_a_μg": number, '
                            '"vitamin_c_mg": number, '
                            '"vitamin_d_μg": number, '
                            '"vitamin_e_mg": number, '
                            '"vitamin_k_μg": number, '
                            '"vitamin_b1_mg": number, '
                            '"vitamin_b2_mg": number, '
                            '"vitamin_b3_mg": number, '
                            '"vitamin_b5_mg": number, '
                            '"vitamin_b6_mg": number, '
                            '"vitamin_b7_μg": number, '
                            '"vitamin_b9_μg": number, '
                            '"vitamin_b12_μg": number'
                        '}, '
                        '"minerals": {'
                            '"calcium_mg": number, '
                            '"iron_mg": number, '
                            '"magnesium_mg": number, '
                            '"phosphorus_mg": number, '
                            '"potassium_mg": number, '
                            '"sodium_mg": number, '
                            '"zinc_mg": number, '
                            '"copper_mg": number, '
                            '"manganese_mg": number, '
                            '"selenium_μg": number, '
                            '"iodine_μg": number, '
                            '"fluoride_μg": number'
                        '}'
                    '}'
                '}'
            '], '
            '"total": {'
                '"calories_kcal": number, '
                '"allergens": ["string", ...], '
                '"macronutrients": {'
                    '"protein_g": number, '
                    '"fat_g": number, '
                    '"saturated_fat_g": number, '
                    '"trans_fat_g": number, '
                    '"monounsaturated_fat_g": number, '
                    '"polyunsaturated_fat_g": number, '
                    '"carbs_g": number, '
                    '"fiber_g": number, '
                    '"sugars_g": number, '
                    '"starch_g": number, '
                    '"cholesterol_mg": number, '
                    '"water_g": number'
                '}, '
                '"micronutrients": {'
                    '"vitamins": {'
                        '"vitamin_a_μg": number, '
                        '"vitamin_c_mg": number, '
                        '"vitamin_d_μg": number, '
                        '"vitamin_e_mg": number, '
                        '"vitamin_k_μg": number, '
                        '"vitamin_b1_mg": number, '
                        '"vitamin_b2_mg": number, '
                        '"vitamin_b3_mg": number, '
                        '"vitamin_b5_mg": number, '
                        '"vitamin_b6_mg": number, '
                        '"vitamin_b7_μg": number, '
                        '"vitamin_b9_μg": number, '
                        '"vitamin_b12_μg": number'
                    '}, '
                    '"minerals": {'
                        '"calcium_mg": number, '
                        '"iron_mg": number, '
                        '"magnesium_mg": number, '
                        '"phosphorus_mg": number, '
                        '"potassium_mg": number, '
                        '"sodium_mg": number, '
                        '"zinc_mg": number, '
                        '"copper_mg": number, '
                        '"manganese_mg": number, '
                        '"selenium_μg": number, '
                        '"iodine_μg": number, '
                        '"fluoride_μg": number'
                    '}'
                '}'
            '}'
        '}, '
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
