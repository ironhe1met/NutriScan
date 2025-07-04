from app.models.classifier import FoodClassifier

def test_predict_dish():
    classifier = FoodClassifier()
    result = classifier.predict("tests/sample.jpg")

    assert "dish_name" in result
    assert "confidence" in result
    assert 0 <= result["confidence"] <= 1
