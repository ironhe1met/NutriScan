# NutriScan — інструкція для мобільного розробника BroCalories

> **Що змінити:** додати **два HTTP-headers** при виклику `POST /analyze/`.
> **Що отримаємо:** (1) захист endpoint-у — без API-токена випадкові запити не пройдуть; (2) кожне сканування привʼязане до конкретного юзера BroCalories, у нашій адмінці зʼявиться сторінка `/users/<uid>` з повним профілем (імʼя, email, аватарка, дані з Firestore — gender, age, weight, goal, тощо) та історією його сканувань.

---

## 1. Що додати

При кожному `POST` на `https://nutriscan.radarme.com.ua/analyze/` додайте **два** HTTP-headers:

```
Authorization: Bearer <API_TOKEN>
X-User-Id: <firebase_uid>
```

| Header | Що це | Звідки взяти |
|---|---|---|
| `Authorization: Bearer <API_TOKEN>` | Наш ключ доступу до API. Один для всього додатку. | `<API_TOKEN>` передамо вам окремо через захищений канал (Bitwarden / Signal). Зберігайте у secure storage додатку. |
| `X-User-Id: <firebase_uid>` | Поточний UID юзера з Firebase Authentication (28-символьна строка). | `FirebaseAuth.instance.currentUser?.uid` |

Body запиту і JSON-відповідь **не міняються** — тільки два нові headers.

### Як виглядає реальний запит (curl)

Це для тестування з терміналу або як reference нашого API-контракту:

```bash
curl -X POST https://nutriscan.radarme.com.ua/analyze/ \
  -H "Authorization: Bearer YOUR_API_TOKEN_HERE" \
  -H "X-User-Id: 7Bx9zP3mKqY8wNsA2fLgVcEhRtUi" \
  -F "image=@/path/to/food.jpg"
```

Як реалізувати ці headers у вашому стеку — на ваш розсуд (Flutter, FlutterFlow, нативно — без різниці).

### Перехідний період

Щоб не зламати юзерів які лишаться зі старою версією додатку:

- **Зараз** — обидва headers **опціональні**: запити без них поки що йдуть, але потрапляють у `anonymous`-bucket.
- **Через ~2 тижні** (як нова версія розкотиться у Google Play / App Store) — `Authorization` стане **обовʼязковим**. Запити без токена будуть отримувати **HTTP 401**.

Перехід зробимо синхронізовано — заздалегідь домовимось про дату.

Відповідь — звичайний JSON (як зараз приходить у ваш додаток):

```json
{
  "data": {
    "dish_name": "Pepsi Cola (500ml bottle)",
    "ingredients": [
      {
        "name": "Pepsi",
        "weight_g": 500,
        "calories_kcal": 215,
        "macronutrients": {"protein_g": 0, "fat_g": 0, "carbs_g": 56.5},
        "allergens": []
      }
    ],
    "total": {
      "calories_kcal": 215,
      "macronutrients": {"protein_g": 0, "fat_g": 0, "carbs_g": 56.5, "water_g": 0},
      "allergens": []
    }
  },
  "error": null
}
```

Response-headers (FYI, інформаційні — мобільному додатку обробляти не треба):
- `X-Provider: anthropic` — який AI обробив (anthropic / openai / google)
- `X-Model: haiku` — яка модель
- `X-Attempts: 1` — з якої спроби вдалось
- `X-Fallback-From: ...` — якщо primary провайдер впав і fallback спрацював

---

## 2. Що відбувається на нашому боці

1. Записуємо `mobile_user_id = <uid>` у БД разом зі скананням.
2. Якщо для цього UID нема профілю в кеші (або старіший за 24 години) — асинхронно тягнемо з Firebase Auth + Firestore `users/{uid}`. Це **не блокує** ваш запит — відповідь приходить як завжди швидко.
3. У нашій адмінці зʼявляється сторінка юзера з повним профілем і його історією сканів. Жодних даних мобільному додатку назад не повертаємо.

---

## 3. Edge cases

| Ситуація | Що шлемо | Що буде (зараз) | Що буде (після переходу на mandatory) |
|---|---|---|---|
| Юзер залогінений, обидва headers | `Authorization` + `X-User-Id` | усе як описано вище — повна привʼязка | те саме |
| Юзер **не залогінений** (Auth нема) | тільки `Authorization` (без `X-User-Id`) | скан йде, але як `anonymous` | те саме |
| Тільки `X-User-Id`, без `Authorization` | (старий клієнт без токена) | скан йде як `anonymous` | **HTTP 401** |
| Жодного header | (старий клієнт) | скан йде як `anonymous` | **HTTP 401** |
| Невалідний / прострочений `Authorization` | поганий токен | сприймається як `anonymous` | **HTTP 401** |
| Помилка з Firebase у нас | (без різниці) | scan все одно обробляється; профіль просто порожній | те саме |

**Підсумок:** `X-User-Id` залишається опціональним (бо юзер може бути не залогінений). `Authorization` спочатку теж опціональний, потім — обовʼязковий.

---

## 4. Як перевірити що працює

Після релізу нової версії з цим змінами — зробіть один тестовий скан з мобільного. Потім скажіть мені (або зайдіть у нашу адмінку):

🌐 https://nutriscan.radarme.com.ua/users — у списку зʼявиться новий рядок з вашим іменем/аватаркою (замість маски `7Bx9zP…RtUi`).

Якщо щось не так — пришліть один UID для перевірки, я подивлюся прямо в БД.

---

## 5. Підсумок

- **Два headers** при `POST /analyze/`: `Authorization: Bearer <API_TOKEN>` (захист) + `X-User-Id: <firebase_uid>` (привʼязка до юзера).
- **`<API_TOKEN>`** ми передамо вам через захищений канал (Bitwarden / Signal). Один на весь додаток.
- **Контракт API** інакше не міняється — body і JSON-відповідь ті ж самі.
- **Перехід на mandatory `Authorization`** — ~2 тижні після релізу нової версії, дату узгоджуємо разом.
- **Жодних SDK / depencies** на вашому боці не треба ставити.
