from app.models.detector import IngredientDetector
import os

def test_detect_ingredients():
    detector = IngredientDetector("models/yolov8x-seg.pt")
    image_path = "tests/test_image.jpg"

    assert os.path.exists(image_path), f"Файл {image_path} не знайдено"

    result = detector.detect(image_path)

    assert isinstance(result, dict), "Результат має бути словником"
    assert "ingredients" in result, "Ключ 'ingredients' відсутній"
    ingredients = result["ingredients"]

    assert isinstance(ingredients, list), "'ingredients' має бути списком"
    assert len(ingredients) > 0, "Список інгредієнтів порожній"

    for item in ingredients:
        assert "name" in item, "Інгредієнт не має поля 'name'"
        assert "confidence" in item, "Інгредієнт не має поля 'confidence'"
        assert isinstance(item["confidence"], float), "'confidence' має бути числом"
