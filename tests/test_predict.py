from app.models.classifier import FoodClassifier

classifier = FoodClassifier()
result = classifier.predict("tests/test_image.jpg")
print(result)
