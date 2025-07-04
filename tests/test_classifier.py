from app.models.classifier import FoodClassifier

def test_predict_dish():
    classifier = FoodClassifier()
    result = classifier.predict("tests/test_image.jpg")

    assert "dish_name" in result
    assert "confidence" in result
    assert 0 <= result["confidence"] <= 1
