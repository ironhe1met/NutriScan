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
