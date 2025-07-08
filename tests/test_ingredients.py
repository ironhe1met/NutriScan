from app.models.detector import IngredientDetector
import os

def test_detect_ingredients():
    detector = IngredientDetector("models/yolov8x-seg.pt")
    image_path = "tests/test_image.jpg"

    assert os.path.exists(image_path), f"Файл {image_path} не знайдено"

    result = detector.detect(image_path)

    assert isinstance(result, list), "Результат має бути списком"
    assert len(result) > 0, "Список інгредієнтів порожній"

    for item in result:
        assert "name" in item, "Інгредієнт не має поля 'name'"
        assert "confidence" in item, "Інгредієнт не має поля 'confidence'"
        assert isinstance(item["confidence"], float), "'confidence' має бути числом"
