# NutriScan — Open Questions

Priority: 🔴 high (blocks architecture/security decisions) · 🟡 medium (important but not blocking) · ⚪ low (later)

---

## Q-001 🔴 — Скільки користувачів у BroCalories зараз і за квартал?

**Контекст:** Потрібно для рішень про rate-limiting, scaling SQLite → PostgreSQL, прайс-планування AI-токенів.
**Зараз:** прод-навантаження ~80-110 запитів/день (з усіх клієнтів сумарно).
**Кому:** product owner.

## Q-002 🔴 — Як автентифікувати запити з BroCalories до `POST /analyze/`?

**Контекст:** Зараз `POST /analyze/` **відкритий** — нема API-key, нема OAuth, нема нічого. Хто завгодно з URL може спалювати наші AI-кредити. Зараз нас рятує те, що URL не публічний (нема SEO, нема reverse-engineering мобільного APK), але це обмеження «безпека через невидимість».
**Варіанти:**
- (a) API key per app version, embedded у мобільний (відомі, але потрібен)
- (b) JWT з підписаним per-user токеном (mobile робить login → отримує token)
- (c) HMAC підпис тіла запиту з shared secret
**Кому:** product owner + Architect-агент. Блокує v1.2.

## Q-003 🟡 — Prompt caching у Anthropic — використовуємо чи ні?

**Контекст:** Влиає на структуру `requests` table у v1.1 Phase 1 (чи додавати `cache_read_tokens` колонку). System prompt у `app/prompt.py` ~180 рядків — кешувати має сенс (~75% input-токенів cacheable).
**Зараз:** Audit показав — **caching не активний** (just stateless calls).
**Кому:** Architect — оцінити impact на cost.

## Q-004 🟡 — Bot user prefs (`/settings`-вибір провайдера) — лишити в memory чи в БД?

**Контекст:** Зараз `user_prefs` — Python dict у пам'яті бота (`bot/telegram.py:30`). При кожному рестарті сервісу — губляться. Користувачі повинні наново обирати провайдер/модель.
**Варіанти:**
- (a) Залишити (бот рідко рестартується, юзерів мало) — KISS
- (b) Зберігати в `bot_prefs` table SQLite — дрібна задача
**Кому:** product owner.

## Q-005 🟡 — При fallback використовувати default-модель наступного провайдера, чи мапити?

**Контекст:** Зараз: користувач хоче `google/pro`, він фейлиться → fallback зайде в openai з default `gpt4o` (не `gpt4o-mini`, не зважаючи на рангу-вибір). Це може бути несподіванкою якщо різниця в швидкості/якості важлива для UX.
**Варіанти:**
- (a) Залишити як є (default — найкраща модель кожного провайдера)
- (b) Маппінг "premium → premium, mini → mini" (треба узгодити tiers між Anthropic/OpenAI/Google)
**Кому:** product owner + Architect.

## Q-006 🟡 — Бекапи `data/stats.db` і `data/images/`?

**Контекст:** Зараз нічого не бекапиться. Втрата серверу = втрата всіх запитів і фоток. Як urgent — питання нерозв'язане.
**Варіанти:** rsync до іншого сервера nightly, або pg_dump якщо мігруємо на PG, або хоч tar до Hetzner Storage Box.
**Кому:** DevOps-агент.

## Q-007 ⚪ — Apple App Store випуск BroCalories?

**Контекст:** Зараз тільки Google Play (Android). Apple — не у планах "поки що" (явно сказано product owner-ом 2026-05-06).
**Кому:** product owner — переглянути коли будуть ресурси.

## Q-008 ⚪ — Multi-tenancy для майбутніх кінцевих юзерів?

**Контекст:** Якщо BroCalories буде продаватись як SaaS іншим компаніям — треба буде ізолювати дані. Зараз НЕ потрібно (один клієнт, один tenant).
**Кому:** product owner — стратегічне рішення на майбутнє.

## Q-009 🟡 — Як визначається `tier` (free/paid) для BroCalories користувача?

**Контекст:** v1.3 вводить tier-based model selection (paid → Sonnet, free → Haiku). Звідки backend дізнається tier конкретного запиту?
**Варіанти:**
- (a) **Per-client token** — окремі токени для "BroCalories free pool" і "BroCalories paid pool". Мобільний app шле відповідний токен в залежності від статусу підписки користувача. Backend дивиться на `clients.tier`.
- (b) **Per-user auth + per-user tier** — потрібна таблиця `users` (BroCalories user-id), tier у `users.tier`. Mobile шле `Authorization: Bearer <user_token>`. Складніше, але точніше.
- (c) **Header `X-User-Tier: free|paid`** — мобільний шле напряму. Просто, але юзер може підмінити (ризик).
**Кому:** product owner — вирішити чи в v1.3 ми вже маємо per-user auth (тоді b), чи робимо швидко (a).

## Q-010 🟡 — Адмін-юзер з `.env` після міграції в БД — що робити?

**Контекст:** v1.2 переносить `ADMIN_USERS` з `.env` у БД. Якщо в `.env` залишається запис, а в БД він уже є — який джерело правди?
**Варіанти:**
- (a) **БД авторитетна,** `.env` — emergency fallback (читається тільки якщо БД пуста або зламана). Зміна в `.env` не впливає на activeпрод.
- (b) **`.env` = seed на старті,** після першого деплою чистимо `.env` від паролів (лишаємо `ADMIN_BOOTSTRAP=email:pass` тільки для надзвичайних випадків).
- (c) `.env` синкається в БД при кожному рестарті (ризик: видалив через UI → повернеться).
**Кому:** product owner. Я б рекомендував (a).

## Q-011 ⚪ — При fallback paid-юзера — теж paid модель з наступного провайдера, чи можна скотитись у free?

**Контекст:** v1.3 fallback. Користувач paid → primary (anthropic/sonnet) фейлиться → fallback OpenAI. Беремо `gpt4o` (paid mapping) чи `gpt4o-mini` (cheaper)?
**Варіанти:**
- (a) Залишаємо tier — paid → paid модель будь-де
- (b) Можна скотитись у free якщо paid недоступна (зекономити, але юзер може помітити погіршення якості)
**Кому:** product owner — стратегічне рішення. Я б за (a).

## Q-012 🟡 — Які саме поля з Firebase треба тягнути для mobile_users?

**Контекст:** v1.2 інтегрує Firebase Admin SDK для розпізнавання BroCalories користувачів. Що саме з Firebase Auth + Firestore documentу нам треба?
**Кандидати:**
- `email`, `displayName`, `photoURL` — з Firebase Auth (стандартно)
- `subscription_status` (free/paid) — мабуть у Firestore document `users/{uid}`
- `created_at`, `last_login` — з Firebase Auth
- Custom claims (якщо є) — для tier (free/paid)
**Кому:** mobile-розробник BroCalories — підтвердити структуру Firestore і де лежить subscription.

## Q-013 🟡 — Firebase service-account credentials — як зберігати?

**Контекст:** Firebase Admin SDK потребує JSON service account з приватним ключем (~2KB). Зараз `.env` містить тільки прості key=value.
**Варіанти:**
- (a) Окремий файл `data/firebase-service-account.json`, шлях у `.env` (`FIREBASE_CRED_PATH`). Файл .gitignored.
- (b) Base64-encoded JSON в одному рядку `.env` (`FIREBASE_CRED_B64=...`). Парсимо у конфіг.
- (c) Vault / Secrets Manager — overkill для одного сервера.
**Кому:** product owner — security trade-off. Я б за (a) як просте і явне.

## Q-014 🟡 — Default model = `haiku` — чи є ризик якості?

**Контекст:** Перемикаємо default з `sonnet` ($3/$15 per M) на `haiku` ($0.80/$4 per M) — економія ~75%. Але Haiku 4.5 хоч і свіжіший за Sonnet 3.5, для food vision може бути менш точним.
**Перевірка перед перемиканням:**
- Прогнати ~20 свіжих фоток через обидві моделі, порівняти `dish_name` і `ingredients_count` — чи Haiku видає схожу якість.
- Або A/B на проді: 20% запитів на Haiku, моніторити failure rate і користувацький feedback.
**Кому:** product owner — чи ризикуємо якістю заради економії, чи краще одразу tier-based (v1.3) з paid → Sonnet.

## Q-015 🟡 — Subscription status — у Firestore чи у RevenueCat?

**Контекст:** На скріншоті GCP Service Accounts видно SA `revenuecat-brocalorie@calorietracker-a194c.iam.gserviceaccount.com` — отже підписки BroCalories керуються через **RevenueCat**, а не безпосередньо у Firestore. Для v1.3 (tier-based models) нам треба десь брати `subscription_tier` (free / paid).
**Варіанти джерела:**
- (a) **Firestore field** що синхронізується з RevenueCat через webhook (тоді ми просто читаємо `users/{uid}.subscription_tier` через наш read-only SA — нічого додаткового)
- (b) **Firebase Auth custom claims** — `auth.get_user(uid).custom_claims["tier"]` (теж читається через наш SA)
- (c) **RevenueCat API напряму** — нам треба окремий RevenueCat API key, окрема залежність, більше складності
**Кому:** mobile-розробник BroCalories. Питання вже в [`firebase-integration-brief.md`](firebase-integration-brief.md), додатково підкреслити RevenueCat.
