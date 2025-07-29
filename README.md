# 📘 Технічне завдання — NutriScan

## 🌟 Мета

Створити локальний AI-сервіс на Ubuntu 22.04, який:

1. Приймає фото страви через FastAPI
2. Передає зображення до GPT-4 Vision (через API OpenAI)
3. Отримує розпізнані інгрідієнти з вагою, калоріями, БЖУ
4. Повертає клієнту готову JSON-відповідь

---

## 🔧 Етапи реалізації

---

## 🧹 Етап 1 — Базовий FastAPI сервер

### ✅ Ціль

Побудувати сервер, який приймає зображення через POST-запит.

### 🗒 Вхід

```
POST /upload/
multipart/form-data
Поле: image
```

### 📄 Вихід

```json
{ "message": "Image received", "filename": "some_image.jpg" }
```

### 🛠 Інструменти

* FastAPI, Pydantic
* Uvicorn
* Python 3.10+

### 🔎 Перевірка

* Сервер запускається
* Зображення зберігається у `tmp/`

---

## 🧹 Етап 2 — Скрипт для запиту до OpenAI Vision

### ✅ Ціль

Створити окрему функцію `analyze_image_base64()`, яка:

* отримує base64-картинку
* надсилає її до GPT-4 Vision
* повертає сирий вивід

### 🗒 Вхід

```python
image_base64: str
```

### 📄 Вихід

```json
{
  "raw_response": "На зображенні видно куряче філе (120г) та броколі (80г)..."
}
```

### 🛠 Інструменти

* OpenAI SDK (або `requests`)
* `.env` з ключем `OPENAI_API_KEY`

### 🔎 Перевірка

* Вивід з GPT-4 Vision повертається

---

## 🧹 Етап 3 — Конвертація зображення в base64

### ✅ Ціль

Реалізувати функцію `image_to_base64(image_path: str) -> str`

### 🗒 Вхід

`image.jpg`

### 📄 Вихід

```python
"data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD..."
```

### 🔎 Перевірка

* Перевірка повертає результат base64 URL

---

## 🧹 Етап 4 — Обробка відповіді GPT та парсинг у JSON

### ✅ Ціль

Створити `parse_openai_response(text: str) -> dict`, яка повертає:

```json
{
  "ingredients": [
    {
      "name": "chicken breast",
      "weight_g": 120,
      "calories_kcal": 198,
      "protein_g": 36,
      "fat_g": 4,
      "carbs_g": 0
    }
  ],
  "total": {
    "calories_kcal": 198,
    "protein_g": 36,
    "fat_g": 4,
    "carbs_g": 0
  }
}
```

### 🔎 Перевірка

* Опрацьований текст повертається у JSON-форматі

---

## 🧹 Етап 5 — Інтеграція FastAPI + OpenAI Vision

### ✅ Ціль

Додати роут `/analyze/`, який:

1. приймає зображення
2. конвертує у base64
3. відсилає до OpenAI Vision
4. обробляє відповідь
5. видає JSON

### 🗒 Вхід

```
POST /analyze/ з image
```

### 📄 Вихід (JSON)

```json
{
  "ingredients": [
    {
      "name": "apple",
      "weight_g": 150,
      "calories_kcal": 78,
      "protein_g": 0.4,
      "fat_g": 0.3,
      "carbs_g": 20
    },
    {
      "name": "banana",
      "weight_g": 120,
      "calories_kcal": 105,
      "protein_g": 1.3,
      "fat_g": 0.3,
      "carbs_g": 27
    }
  ],
  "total": {
    "calories_kcal": 183,
    "protein_g": 1.7,
    "fat_g": 0.6,
    "carbs_g": 47
  }
}
```

### 🔎 Перевірка

* Повертається коректний JSON

---

## 🥮 Етап 6 — Логування, обробка помилок, кеш

### ✅ Ціль

* Додати логування усіх запитів
* Обробляти помилки OpenAI/відсутні ключі
* (Опційно) кешування останн

---

## 🥮 Тестування через curl
```bash
curl -X POST -F image=@dish.jpg http://localhost:8000/analyze/
```

📄 Ліцензія
Цей проєкт поширюється під ліцензією MIT.

---

## 📁 Структура проєкту:
```python
nutriscan/
├── app/
│   ├── main.py
│   └── utils/
├── tmp/                ← зберігання зображень
├── requirements.txt    ← оновлюється поступово
```