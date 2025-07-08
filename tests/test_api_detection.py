import os
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_detect_ingredients():
    image_path = "tests/test_image.jpg"
    assert os.path.exists(image_path), f"Файл {image_path} не знайдено"

    with open(image_path, "rb") as f:
        response = client.post("/detect/", files={"image": ("filename.jpg", f, "image/jpeg")})

    assert response.status_code == 200
    data = response.json()
    assert "ingredients" in data
    assert isinstance(data["ingredients"], list)
    for item in data["ingredients"]:
        assert "name" in item
        assert "confidence" in item