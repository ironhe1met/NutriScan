import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

pytest.importorskip("httpx")

from nutriscan.api.openfoodfacts import FoodInfoCache


def test_cache_roundtrip(tmp_path):
    db = tmp_path / "cache.db"
    cache = FoodInfoCache(db)
    data = {"calories": 50.0, "proteins": 1.0, "fats": 0.5, "carbs": 10.0}
    cache.set("apple", data)
    assert cache.get("apple") == data
    cache.close()
