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

    # Логування: перевіряємо, чи base64-зображення коректне
    try:
        decoded_image = base64.b64decode(image_base64)
        print("Image decoded successfully, size:", len(decoded_image))
    except Exception as e:
        return {"error": f"Failed to decode base64 image: {str(e)}"}

    system_prompt = (
        "You are an AI food analyzer. Analyze the food in the image.",
        "Ignore humans, faces, hands, and any personal information.",
        "Focus only on food and ingredients.",
        "Break down the dish into its visible and possible ingredients (e.g., for a burger: bun, patty, lettuce, tomato, cheese, sauce, fries).",
        "Identify the dish name, list all ingredients with their estimated weight (in grams), calories, allergens, and all possible macronutrients and micronutrients.",
        "macronutrients: always output (protein_g, fat_g, carbs_g, water_g), output if greater than 0 (saturated_fat_g, trans_fat_g, monounsaturated_fat_g, polyunsaturated_fat_g, fiber_g, sugars_g, starch_g, cholesterol_mg).",
        "micronutrients: vitamins: output if greater than 0 (vitamin_a_μg, vitamin_c_mg, vitamin_d_μg, vitamin_e_mg, vitamin_k_μg, vitamin_b1_mg, vitamin_b2_mg, vitamin_b3_mg, vitamin_b5_mg, vitamin_b6_mg, vitamin_b7_μg, vitamin_b9_μg, vitamin_b12_μg), minerals: output if greater than 0 (calcium_mg, iron_mg, magnesium_mg, phosphorus_mg, potassium_mg, sodium_mg, zinc_mg, copper_mg, manganese_mg, selenium_μg, iodine_μg, fluoride_μg).",
        "Always include the allergens field for each ingredient and the total, even if empty (use an empty array [] if no allergens are present).",
        "Calculate totals for the whole dish, including only the nutrients present in the ingredients (except for protein_g, fat_g, carbs_g, water_g, which must always be included, even if 0).",
        "Provide realistic estimates based on standard portion sizes for fast food.",
        "Respond strictly in JSON format only, without any explanations, comments, markdown, or code blocks.",
        "All keys and values must be in English."
        "Final JSON structure:"
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
                        '"carbs_g": number, '
                        '"water_g": number, '
                    '}, '
                    '"micronutrients": {'
                        '"vitamins": {}, '
                        '"minerals": {}'
                    '}'
                '}'
            '], '
            '"total": {'
                '"calories_kcal": number, '
                '"allergens": ["string", ...], '
                '"macronutrients": {'
                    '"protein_g": number, '
                    '"fat_g": number, '
                    '"carbs_g": number, '
                    '"water_g": number'
                '}, '
                '"micronutrients": {'
                    '"vitamins": {}, '
                    '"minerals": {}'
                '}'
            '}'
        '}'
    )

    try:
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
            max_tokens=2000
        )
    except openai.OpenAIError as e:
        return {"error": f"OpenAI API error: {str(e)}"}

    raw_text = result.choices[0].message.content
    # Логування сирої відповіді
    print("Raw GPT-4o response:", raw_text)
    extracted_json = extract_json_from_text(raw_text)
    # Логування витягнутого JSON
    print("Extracted JSON text:", extracted_json)

    try:
        return json.loads(extracted_json)
    except json.JSONDecodeError:
        return {"raw_response": raw_text, "error": "❌ Не вдалося розпарсити JSON"}

# Тестування локально
if __name__ == "__main__":
    with open("bur.jpeg", "rb") as image_file:
        image_base64 = base64.b64encode(image_file.read()).decode("utf-8")
    result = analyze_image_base64(image_base64)
    print("Final result:", json.dumps(result, indent=2, ensure_ascii=False))
