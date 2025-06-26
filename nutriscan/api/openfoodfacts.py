import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import Any

import requests

DB_PATH = Path("data/cache.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS nutrition (
    ingredient TEXT PRIMARY KEY,
    calories REAL,
    proteins REAL,
    fats REAL,
    carbs REAL
)
"""

API_URL = "https://world.openfoodfacts.org/api/v2/search"


class FoodInfoCache:
    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.conn = sqlite3.connect(db_path)
        self.conn.execute(CREATE_TABLE)

    def get(self, name: str) -> dict[str, Any] | None:
        cur = self.conn.execute(
            "SELECT calories, proteins, fats, carbs FROM nutrition WHERE ingredient=?",
            (name,),
        )
        row = cur.fetchone()
        if row:
            return {
                "calories": row[0],
                "proteins": row[1],
                "fats": row[2],
                "carbs": row[3],
            }
        return None

    def set(self, name: str, info: dict[str, Any]) -> None:
        self.conn.execute(
            "REPLACE INTO nutrition (ingredient, calories, proteins, fats, carbs) VALUES (?, ?, ?, ?, ?)",
            (
                name,
                info.get("calories"),
                info.get("proteins"),
                info.get("fats"),
                info.get("carbs"),
            ),
        )
        self.conn.commit()


def fetch_info(name: str) -> dict[str, Any] | None:
    params = {"search_terms": name, "page_size": 1, "fields": "nutriments"}
    resp = requests.get(API_URL, params=params, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        products = data.get("products")
        if products:
            nutriments = products[0].get("nutriments", {})
            return {
                "calories": nutriments.get("energy-kcal_100g"),
                "proteins": nutriments.get("proteins_100g"),
                "fats": nutriments.get("fat_100g"),
                "carbs": nutriments.get("carbohydrates_100g"),
            }
    return None


cache = FoodInfoCache()


def get_nutrition(name: str) -> dict[str, Any] | None:
    info = cache.get(name)
    if info:
        return info
    info = fetch_info(name)
    if info:
        cache.set(name, info)
    return info
