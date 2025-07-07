# 📘 Технічне завдання — NutriScan AI-сервіс

Мета: Розробити локальний AI-сервіс на Ubuntu 22.04, який:

1. Приймає фото страви через API
2. Визначає інгредієнти
3. Оцінює масу (вагу)
4. Розраховує калорійність і макроелементи (БЖУ)
5. Повертає JSON-відповідь

## 🧹 Етап 1: Створення базового API

🌟 Мета
Налаштувати FastAPI-сервер, який приймає POST-запит з фото.

📅 Вхід
POST /upload/ з multipart/form-data, поле image

📄 Вихід

```
{ "message": "Image received", "filename": "some_image.jpg" }
```

🛠 Інструменти

* FastAPI
* Pydantic
* Uvicorn

✅ Критерії завершення

* Сервер запускається
* Фото приймається та зберігається в тимчасовій папці
* Написано автотест: test\_upload.py

## 🧹 Етап 2: Визначення інгредієнтів

🌟 Мета
Підключити модель YOLOv8x-seg для детекції інгредієнтів на фото.

📅 Вхід
Фото страви (локальний файл)

📄 Вихід

```
{
  "ingredients": [
    {"name": "potato", "confidence": 0.88},
    {"name": "carrot", "confidence": 0.81}
  ]
}
```

🛠 Інструменти

* Модель YOLOv8x-seg (`yolov8x-seg.pt`)
* Ultralytics YOLO
* Torch
* OpenCV

✅ Критерії завершення

* Модель працює локально (`models/detector.py`)
* Написано скрипт перевірки `tests/test_ingredients.py`
* Результат по одному тестовому зображенню

## 🧹 Етап 3: Інтеграція API + Модель інгредієнтів

🌟 Мета
Фото з API передається в модель, результат повертається користувачу.

📅 Вхід
POST /detect/ з фото

📄 Вихід

```
{
  "ingredients": [
    {"name": "potato", "confidence": 0.88},
    {"name": "carrot", "confidence": 0.81}
  ]
}
```

✅ Критерії завершення

* Повна передача зображення через API в модель
* Автотест test\_api\_detection.py

## 🧹 Етап 4: Оцінка маси інгредієнтів

🌟 Мета
Оцінити приблизну вагу інгредієнтів на основі розміру.

📅 Вхід
Фото + bounding boxes інгредієнтів

📄 Вихід

```
{
  "ingredients": [
    {"name": "carrot", "weight_g": 50},
    {"name": "potato", "weight_g": 100}
  ]
}
```

🛠 Інструменти

* Евристика за площею об'єкта
* Kalman або регресійна модель (опціонально)

✅ Критерії завершення

* Розрахунок ваги працює
* Автотест test\_weight\_estimation.py

## 🧹 Етап 5: Розрахунок калорійності і БЖУ

🌟 Мета
На основі назви інгредієнтів і ваги розрахувати калорії, білки, жири, вуглеводи.

📅 Вхід
JSON з інгредієнтами та вагою

📄 Вихід

```
{
  "total": {
    "calories_kcal": 350,
    "protein_g": 12,
    "fat_g": 8,
    "carbs_g": 45
  }
}
```

🛠 Інструменти

* Open Food Facts API
* Кешування локально (SQLite)

✅ Критерії завершення

* Дані приходять з OFF
* Тест із відомим набором інгредієнтів test\_nutrition\_calc.py

## 🧹 Етап 6: Інтеграція всього конвеєра

🌟 Мета
Об’єднати всі етапи в один API-ендпоінт /analyze/, який приймає фото і повертає фінальний JSON.

📅 Вхід
POST /analyze/ з фото

📄 Вихід (приклад):

```
{
  "ingredients": [
    { "name": "potato", "weight_g": 100, "calories_kcal": 77, "protein_g": 2, "fat_g": 0.1, "carbs_g": 17 },
    { "name": "carrot", "weight_g": 50, "calories_kcal": 20, "protein_g": 0.5, "fat_g": 0.1, "carbs_g": 4.7 }
  ],
  "total": {
    "calories_kcal": 97,
    "protein_g": 2.5,
    "fat_g": 0.2,
    "carbs_g": 21.7
  }
}
```

✅ Критерії завершення

* Все зібрано в одне
* Пройдені інтеграційні тести test\_full\_pipeline.py





## 📁 Структура проєкту NutriScan (v0.2)

```
nutriscan/
├── app/                       # Основна логіка FastAPI
│   ├── main.py               # Точка входу FastAPI
│   ├── models/               # Модель інгредієнтів (YOLOv8 та ін.)
│   │   └── detector.py
│   ├── services/             # Логіка по вагам, БЖУ, тощо
│   │   └── nutrition.py
│   ├── utils/                # Обробка зображень, допоміжне
│   │   └── image_utils.py
│   └── api/                  # Роути
│       └── routes.py
│
├── tests/                    # Pytest тести на всі етапи
│   ├── test_upload.py
│   ├── test_ingredients.py
│   ├── test_api_detection.py
│   ├── test_weight_estimation.py
│   └── test_nutrition_calc.py
│
├── models/                   # Ваги моделей (.pt, .bin тощо)
│   └── detector.pt
│
├── scripts/                  # Скрипти інсталяції/запуску
│   ├── install.sh            # Встановлення залежностей, моделей
│   ├── download_models.sh    # Завантаження ваг
│   └── run_server.sh         # Запуск FastAPI
│
├── docs/                     # Документація
│   ├── DEVLOG.md             # Dev-блог по етапах
│   └── INSTALL.md            # Інструкція встановлення
│
├── .env                      # Змінні середовища (якщо потрібно)
├── requirements.txt
└── README.md
```


📌 Команди на майбутнє

| Дія        | Команда                            |
| ---------- | ---------------------------------- |
| Перезапуск | `sudo systemctl restart nutriscan` |
| Стоп       | `sudo systemctl stop nutriscan`    |
| Статус     | `sudo systemctl status nutriscan`  |
| Логи       | `journalctl -u nutriscan -f`       |
