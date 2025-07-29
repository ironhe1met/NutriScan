# 📘 Технічне завдання — NutriScan

## 🌟 Мета

Створити AI-сервіс на Ubuntu 22.04, який:

1. Приймає фото страви через FastAPI
2. Передає зображення до GPT-4 Vision (через API OpenAI)
3. Отримує розпізнані інгрідієнти з вагою, калоріями, БЖУ
4. Повертає клієнту готову JSON-відповідь

---

## 🔧 Етапи реалізації


## 🥮 Етап 1 — Базовий FastAPI сервер

### ✅ Ціль

Побудувати сервер, який приймає зображення через POST-запит.

### 🗒 Вхід

```
POST /analyze/
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

## 🥮 Етап 2 — Скрипт для запиту до OpenAI Vision

### ✅ Ціль

Створити окрему функцію `analyze_image_base64()`, яка:

* отримує base64-картинку
* надсилає її до GPT-4 Vision
* повертає JSON-вивід

### 🗒 Вхід

```python
image_base64: str
```

### 📄 Вихід

```json
{
  "ingredients": [...],
  "total": {...}
}
```

### 🛠 Інструменти

* OpenAI SDK
* `.env` з ключем `OPENAI_API_KEY`

### 🔎 Перевірка

* Вивід з GPT-4 Vision у форматі JSON

---

## 🥮 Етап 3 — Конвертація зображення в base64

### ✅ Ціль

Реалізувати функцію `image_to_base64(image_path: str) -> str`

### 🗒 Вхід

`image.jpg`

### 📄 Вихід

```python
"data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD..."
```

### 🔎 Перевірка

* Повертається коректний base64 URL

---

## 🥮 Етап 4 — Обробка відповіді GPT та парсинг у JSON

### ✅ Ціль

* GPT-4 Vision повертає чистий JSON (через промт)
* Парсинг виконується без додаткових функцій

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

* JSON структура збігається з очікуваною схемою

---

## 🥮 Етап 5 — Інтеграція FastAPI + OpenAI Vision

### ✅ Ціль

Додати роут `/analyze/`, який:

1. приймає зображення
2. конвертує у base64
3. відсилає до OpenAI Vision
4. обробляє відповідь
5. повертає JSON

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

## 🥮 Етап 6 — Логування, обробка помилок

### ✅ Ціль

* Додати логування всіх запитів через `logger.py`
* Обробляти помилки (відсутній ключ, помилки OpenAI)
* Повертати `HTTPException` з кодом та повідомленням

### 🔎 Перевірка

* Усі запити логуються
* Помилки не валять сервер

---

## 🥮 Тестування через curl
```bash
curl -X POST -F image=@dish.jpg http://localhost:8000/analyze/
```

---

## 📄 Ліцензія

Цей проєкт поширюється під ліцензією MIT.

---

## 📁 Структура проєкту:
```bash
NutriScan/
├── app/
│   ├── __init__.py
│   ├── main.py             # Точка входу FastAPI
│   ├── routes.py           # Роути API (наприклад /analyze/)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── image_utils.py   # Конвертація зображень у base64
│   │   └── openai_client.py # Запит до OpenAI Vision API
│   └── logger.py           # Логування
├── tmp/                    # Тимчасові зображення
├── tests/                  # Юніт-тести (опціонально)
│   ├── check_openai_access.py
│   └── test_openai_client.py
├── .env                    # OPENAI_API_KEY
├── requirements.txt        # Залежності
├── LICENSE                 # MIT License
├── README.md               # Документація
└── install.sh              # Скрипт встановлення systemd
```
