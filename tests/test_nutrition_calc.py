# tests/test_nutrition_calc.py

def test_nutrition_enrichment():
    from app.services.nutrition import NutritionService

    service = NutritionService()
    input_data = [
        {"name": "apple", "weight_g": 150},
        {"name": "carrot", "weight_g": 50}
    ]
    result = service.enrich_ingredients(input_data)

    assert "ingredients" in result
    assert "total" in result
    assert len(result["ingredients"]) == 2
    assert result["total"]["calories_kcal"] > 0
