import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
assert api_key, "❌ OPENAI_API_KEY не знайдено"

headers = {
    "Authorization": f"Bearer {api_key}"
}

response = requests.get("https://api.openai.com/v1/models", headers=headers)
response.raise_for_status()

models = [m["id"] for m in response.json()["data"]]
print("\n✅ Доступні моделі:")
for m in models:
    print("-", m)

# Перевірка наявності GPT-4 Vision
has_vision = any("gpt-4-vision" in m for m in models)
print("\n🔍 GPT-4 Vision:", "є доступ" if has_vision else "немає доступу")
