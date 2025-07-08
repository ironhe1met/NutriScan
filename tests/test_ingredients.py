from app.models.detector import IngredientDetector

if __name__ == "__main__":
    detector = IngredientDetector()
    result = detector.detect("tests/test_image.jpg")
    print(result)