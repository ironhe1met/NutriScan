# NutriScan — Open Questions

Priority: 🔴 high (blocks architecture/security decisions) · 🟡 medium (important but not blocking) · ⚪ low (later)

---

## Q-001 🔴 — Скільки користувачів у BloCalories зараз і за квартал?

**Контекст:** Потрібно для рішень про rate-limiting, scaling SQLite → PostgreSQL, прайс-планування AI-токенів.
**Зараз:** прод-навантаження ~80-110 запитів/день (з усіх клієнтів сумарно).
**Кому:** product owner.

## Q-002 🔴 — Як автентифікувати запити з BloCalories до `POST /analyze/`?

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

## Q-007 ⚪ — Apple App Store випуск BloCalories?

**Контекст:** Зараз тільки Google Play (Android). Apple — не у планах "поки що" (явно сказано product owner-ом 2026-05-06).
**Кому:** product owner — переглянути коли будуть ресурси.

## Q-008 ⚪ — Multi-tenancy для майбутніх кінцевих юзерів?

**Контекст:** Якщо BloCalories буде продаватись як SaaS іншим компаніям — треба буде ізолювати дані. Зараз НЕ потрібно (один клієнт, один tenant).
**Кому:** product owner — стратегічне рішення на майбутнє.
