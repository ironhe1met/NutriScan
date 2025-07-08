from app.models.detector import IngredientDetector

if __name__ == "__main__":
    detector = IngredientDetector("models/yolov8x-seg.pt")
    image_path = "tests/test_image.jpg"
    result = detector.detect(image_path)
    print(result)
