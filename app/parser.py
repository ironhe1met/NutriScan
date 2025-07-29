import json
import re
from typing import Dict, Any


def parse_openai_response(text: str) -> Dict[str, Any]:
    """Parse raw GPT text response into structured JSON.

    The function tries to locate a JSON object within the provided
    text. If totals are missing they are calculated from ingredients.
    """
    text = text.strip()
    data = None

    # Try direct JSON parse
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Look for JSON object within text
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            data = json.loads(match.group(0))

    if not isinstance(data, dict):
        raise ValueError("Could not parse OpenAI response")

    ingredients = data.get("ingredients")
    if isinstance(ingredients, list):
        if "total" not in data:
            total = {"calories_kcal": 0.0, "protein_g": 0.0, "fat_g": 0.0, "carbs_g": 0.0}
            for ing in ingredients:
                total["calories_kcal"] += float(ing.get("calories_kcal", 0))
                total["protein_g"] += float(ing.get("protein_g", 0))
                total["fat_g"] += float(ing.get("fat_g", 0))
                total["carbs_g"] += float(ing.get("carbs_g", 0))
            data["total"] = total
        return data
    else:
        raise ValueError("JSON does not contain 'ingredients'")
