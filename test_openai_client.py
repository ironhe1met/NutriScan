from app.services.openai_client import analyze_image_base64
from pathlib import Path
import base64

# Завантажити тестову картинку
img_path = Path("tmp/test.jpg")
assert img_path.exists(), "Файл tmp/test.jpg не знайдено"

# Конвертувати в base64 data-url
b64 = base64.b64encode(img_path.read_bytes()).decode()
data_url = f"data:image/jpeg;base64,{b64}"

# Виклик функції
print("\n⏳ Запит до GPT-4o Vision...")
result = analyze_image_base64(data_url)

# Вивести результат
print("\n✅ Відповідь GPT-4o Vision:")
print("================================")
print(result["raw_response"])
print("================================")
