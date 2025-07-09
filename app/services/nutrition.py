import requests

DATA_SOURCE = "off"  # "off" або "usda"

# 🔸 OFF
OFF_URL = "https://world.openfoodfacts.org/cgi/search.pl"
OFF_FIELDS = ["product_name", "nutriments"]
OFF_PARAMS = {
    "search_simple": 1,
    "action": "process",
    "json": 1,
    "page_size": 1,
    "fields": ",".join(OFF_FIELDS)
}

# 🔹 USDA (необов'язково)
USDA_API_KEY = "YOUR_USDA_API_KEY"  # ← замінити, якщо потрібно
USDA_SEARCH_URL = "https://api.nal.usda.gov/fdc/v1/foods/search"
USDA_DETAILS_URL = "https://api.nal.usda.gov/fdc/v1/food/"

class NutritionService:

    def __init__(self):
        pass

    def enrich_ingredients(self, ingredients: list):
        enriched = []
        total = {"calories_kcal": 0.0, "protein_g": 0.0, "fat_g": 0.0, "carbs_g": 0.0}

        for item in ingredients:
            name = item["name"]
            weight = item["weight_g"]

            if DATA_SOURCE == "usda":
                nutrients = self._fetch_usda(name)
            else:
                nutrients = self._fetch_off(name)

            if nutrients:
                factor = weight / 100.0
                enriched_item = {
                    "name": name,
                    "weight_g": weight,
                    "calories_kcal": round(nutrients.get("energy-kcal", 0) * factor, 1),
                    "protein_g": round(nutrients.get("proteins", 0) * factor, 2),
                    "fat_g": round(nutrients.get("fat", 0) * factor, 2),
                    "carbs_g": round(nutrients.get("carbohydrates", 0) * factor, 2)
                }
                enriched.append(enriched_item)

                total["calories_kcal"] += enriched_item["calories_kcal"]
                total["protein_g"] += enriched_item["protein_g"]
                total["fat_g"] += enriched_item["fat_g"]
                total["carbs_g"] += enriched_item["carbs_g"]

        total = {k: round(v, 2) for k, v in total.items()}
        return {"ingredients": enriched, "total": total}

    def _fetch_off(self, name: str) -> dict:
        try:
            params = OFF_PARAMS.copy()
            params["search_terms"] = name
            response = requests.get(OFF_URL, params=params, timeout=5)
            data = response.json()

            if data["count"] > 0:
                product = data["products"][0]
                return product.get("nutriments", {})
        except Exception as e:
            print(f"OFF Error for {name}: {e}")
        return {}

    def _fetch_usda(self, name: str) -> dict:
        try:
            search_resp = requests.get(
                USDA_SEARCH_URL,
                params={"query": name, "api_key": USDA_API_KEY, "pageSize": 1},
                timeout=5
            ).json()

            if "foods" not in search_resp or not search_resp["foods"]:
                return {}

            food_id = search_resp["foods"][0]["fdcId"]
            detail_resp = requests.get(
                f"{USDA_DETAILS_URL}{food_id}",
                params={"api_key": USDA_API_KEY},
                timeout=5
            ).json()

            nutrients = {}
            for n in detail_resp.get("foodNutrients", []):
                name = n.get("nutrientName", "").lower()
                val = n.get("value", 0)

                if "energy" in name and "kcal" in name:
                    nutrients["energy-kcal"] = val
                elif "protein" in name:
                    nutrients["proteins"] = val
                elif "fat" in name:
                    nutrients["fat"] = val
                elif "carbohydrate" in name:
                    nutrients["carbohydrates"] = val

            return nutrients
        except Exception as e:
            print(f"USDA Error for {name}: {e}")
        return {}
