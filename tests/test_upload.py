from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_upload_image():
    with open("tests/sample.jpg", "rb") as img:
        response = client.post("/upload/", files={"image": ("sample.jpg", img, "image/jpeg")})
    assert response.status_code == 200
    assert "filename" in response.json()
