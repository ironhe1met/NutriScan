# NutriScan — інструкція для мобільного розробника BroCalories

> **Що змінити:** додати **один HTTP-header** при виклику `POST /analyze/`.
> **Що отримаємо:** кожне сканування буде привʼязане до конкретного юзера BroCalories, у нашій адмінці зʼявиться сторінка `/users/<uid>` з повним профілем (імʼя, email, аватарка, дані з Firestore — gender, age, weight, goal, тощо) та історією його сканувань.

---

## 1. Що додати

При кожному `POST` на `https://nutriscan.radarme.com.ua/analyze/` додайте HTTP-header:

```
X-User-Id: <firebase_uid>
```

де `<firebase_uid>` — це `FirebaseAuth.instance.currentUser?.uid` (28-символьна строка).

### Як виглядає повний HTTP-запит

Це для розуміння контракту — те, що ваш Flutter `http.post` фактично шле по мережі. **До** (як зараз):

```http
POST /analyze/ HTTP/1.1
Host: nutriscan.radarme.com.ua
Content-Type: multipart/form-data; boundary=----dart-boundary-xxx
Content-Length: 20197

------dart-boundary-xxx
Content-Disposition: form-data; name="image"; filename="food.jpg"
Content-Type: image/jpeg

<binary image bytes>
------dart-boundary-xxx--
```

**Після** (треба):

```http
POST /analyze/ HTTP/1.1
Host: nutriscan.radarme.com.ua
X-User-Id: 7Bx9zP3mKqY8wNsA2fLgVcEhRtUi    ← єдина зміна
Content-Type: multipart/form-data; boundary=----dart-boundary-xxx
Content-Length: 20197

<same body>
```

Тобто буквально **один рядок** у HTTP-headers, body не міняється, відповідь не міняється.

### Приклад на Dart / Flutter

```dart
final uid = FirebaseAuth.instance.currentUser?.uid;

final response = await http.post(
  Uri.parse('https://nutriscan.radarme.com.ua/analyze/'),
  headers: {
    if (uid != null) 'X-User-Id': uid,
    // інші headers як були
  },
  body: ...,  // multipart image як зараз
);
```

### Приклад через curl (для тестування з терміналу)

Якщо хочете перевірити прямо з терміналу, без перебудови додатку — скопіюйте і запустіть, замінивши `<UID>` і шлях до фотки:

```bash
curl -X POST https://nutriscan.radarme.com.ua/analyze/ \
  -H "X-User-Id: 7Bx9zP3mKqY8wNsA2fLgVcEhRtUi" \
  -F "image=@/path/to/food.jpg"
```

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

| Ситуація | Що шлемо | Що буде |
|---|---|---|
| Юзер залогінений | header `X-User-Id: <uid>` | усе як описано вище |
| Юзер **не залогінений** | header **не шлемо** (або порожній) | скан йде як `anonymous` — теж OK, не падає |
| Помилка з Firebase у нас | (без різниці) | scan все одно обробляється; профіль просто буде порожній |

Тобто: **header опціональний**. Якщо нема UID — просто не шліть, нічого не зламається.

---

## 4. Як перевірити що працює

Після релізу нової версії з цим змінами — зробіть один тестовий скан з мобільного. Потім скажіть мені (або зайдіть у нашу адмінку):

🌐 https://nutriscan.radarme.com.ua/users — у списку зʼявиться новий рядок з вашим іменем/аватаркою (замість маски `7Bx9zP…RtUi`).

Якщо щось не так — пришліть один UID для перевірки, я подивлюся прямо в БД.

---

## 5. Підсумок

- **1 рядок коду** у Flutter — додати header `X-User-Id`.
- **Контракт API** не міняється — тільки додатковий header.
- **Опціонально** — якщо не передали, працює як зараз (anonymous).
- **Жодних SDK / depencies** на вашому боці не треба ставити.
