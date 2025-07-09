import requests

class NutritionService:
    def __init__(self):
        self.api_url = "https://world.openfoodfacts.org/api/v2/product/"

    def get_off_data(self, ingredient_name: str):
        response = requests.get(
            "https://world.openfoodfacts.org/cgi/search.pl",
            params={
                "search_terms": ingredient_name,
                "search_simple": 1,
                "action": "process",
                "json": 1,
                "page_size": 1,
            },
            timeout=5,
        )

        if response.status_code == 200:
            products = response.json().get("products", [])
            if products:
                nutriments = products[0].get("nutriments", {})
                return {
                    "calories_kcal": round(nutriments.get("energy-kcal_100g", 0), 2),
                    "protein_g": round(nutriments.get("proteins_100g", 0), 2),
                    "fat_g": round(nutriments.get("fat_100g", 0), 2),
                    "carbs_g": round(nutriments.get("carbohydrates_100g", 0), 2)
                }

        return {
            "calories_kcal": 0,
            "protein_g": 0,
            "fat_g": 0,
            "carbs_g": 0
        }

    def enrich_ingredients(self, ingredients: list):
        enriched = []
        total = {"calories_kcal": 0, "protein_g": 0, "fat_g": 0, "carbs_g": 0}

        for item in ingredients:
            nutrition = self.get_off_data(item["name"])
            weight = item["weight_g"] / 100.0

            enriched_item = {
                "name": item["name"],
                "weight_g": item["weight_g"],
                "calories_kcal": round(nutrition["calories_kcal"] * weight, 1),
                "protein_g": round(nutrition["protein_g"] * weight, 2),
                "fat_g": round(nutrition["fat_g"] * weight, 2),
                "carbs_g": round(nutrition["carbs_g"] * weight, 2),
            }

            total["calories_kcal"] += enriched_item["calories_kcal"]
            total["protein_g"] += enriched_item["protein_g"]
            total["fat_g"] += enriched_item["fat_g"]
            total["carbs_g"] += enriched_item["carbs_g"]

            enriched.append(enriched_item)

        total = {k: round(v, 2) for k, v in total.items()}

        return {"ingredients": enriched, "total": total}
