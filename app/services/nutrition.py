# app/services/nutrition.py

import requests
import sqlite3
from typing import Dict, List

class NutritionService:
    def __init__(self, db_path="app/assets/nutrition_cache.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_table()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nutrition_cache (
                name TEXT PRIMARY KEY,
                calories REAL,
                protein REAL,
                fat REAL,
                carbs REAL
            )
        """)
        self.conn.commit()

    def fetch_from_off(self, name: str) -> Dict:
        url = f"https://world.openfoodfacts.org/api/v0/product/{name}.json"
        try:
            r = requests.get(url, timeout=5)
            data = r.json()
            nutr = data.get("product", {}).get("nutriments", {})
            return {
                "calories": nutr.get("energy-kcal_100g", 0),
                "protein": nutr.get("proteins_100g", 0),
                "fat": nutr.get("fat_100g", 0),
                "carbs": nutr.get("carbohydrates_100g", 0)
            }
        except Exception:
            return {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}

    def get_nutrition(self, name: str) -> Dict:
        cursor = self.conn.cursor()
        row = cursor.execute("SELECT * FROM nutrition_cache WHERE name = ?", (name,)).fetchone()

        if row:
            return dict(zip(["name", "calories", "protein", "fat", "carbs"], row))

        data = self.fetch_from_off(name)
        cursor.execute("""
            INSERT OR REPLACE INTO nutrition_cache (name, calories, protein, fat, carbs)
            VALUES (?, ?, ?, ?, ?)
        """, (name, data["calories"], data["protein"], data["fat"], data["carbs"]))
        self.conn.commit()

        return {"name": name, **data}

    def enrich_ingredients(self, ingredients: List[Dict]) -> Dict:
        total = {"calories_kcal": 0, "protein_g": 0, "fat_g": 0, "carbs_g": 0}
        enriched = []

        for item in ingredients:
            info = self.get_nutrition(item["name"])
            weight = item.get("weight_g", 100)

            cals = round(info["calories"] * weight / 100, 1)
            prot = round(info["protein"] * weight / 100, 1)
            fat = round(info["fat"] * weight / 100, 1)
            carbs = round(info["carbs"] * weight / 100, 1)

            total["calories_kcal"] += cals
            total["protein_g"] += prot
            total["fat_g"] += fat
            total["carbs_g"] += carbs

            enriched.append({
                "name": item["name"],
                "weight_g": weight,
                "calories_kcal": cals,
                "protein_g": prot,
                "fat_g": fat,
                "carbs_g": carbs
            })

        total = {k: round(v, 1) for k, v in total.items()}
        return {"ingredients": enriched, "total": total}
