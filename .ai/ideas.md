# NutriScan — Ideas / Roadmap

## v1.1 — observability + UX bundle

Recommended order. Each phase = one PR.

### Phase 1 — DB migration + auth (one PR scope, but token rollout multi-stage)

- [ ] **Tokens + cost stats.** Add columns `input_tokens`, `output_tokens`, `cost_usd` to `requests`. **Snapshot at request time** (not on-the-fly) — history doesn't get rewritten when prices change. Pricing dict per `(provider, model)` in `config.py`. If we already use Anthropic prompt caching — add `cache_read_tokens` column. **UI:** new dashboard cards (Total tokens, Total cost, Avg $/req, Cost/day), columns in By Provider/Model and By Day, `≈$` in History detail. **Old 1572 records:** leave as `—` (no token data → can't even compute with today's price).
- [ ] **Per-client tokens (`clients` table) + API-token auth on `/analyze/`.** New table `clients(id, name, token_hash, status, created_at)`. Endpoint reads `Authorization: Bearer <token>` (or `X-API-Key` — TBD). On match → request tagged with `client_id`, also stored on `requests`.
  - **Rollout (3 фази, без зламу прод):**
    1. **Optional** — приймаємо і з токеном, і без. Без токена → запит проходить + `client_id=NULL` (lognemo як "anonymous"). З токеном → tagged. Дашборд показує "anon vs known" розподіл, видно прогрес адопції.
    2. **Wait for Google Play rollout** — поки 95%+ юзерів не оновлять додаток (зазвичай 1-2 тижні з моменту release). Слідкуємо за "anon" відсотком в дашборді.
    3. **Mandatory** — прибираємо backward-compat. Запити без токена → HTTP 401. У релізі — попереджуючий nginx-rule (logs only) за тиждень до switch, щоб мати точний таймстемп.
  - **Перевага:** замінює "anonymous" rate-limit (30/min IP) на per-client-token rate-limit (можна різний ліміт для BroCalories / TG-bot / partners).
- [ ] **Per-user stats (Telegram).** Add `telegram_user_id` column to `requests`. Без неї не побачимо хто з TG-користувачів спалює бюджет.

### Phase 2 — UI on top of new data

- [ ] **CSV export** buttons on History/Failed (bookkeeping, audits).
- [ ] **Hourly chart for "today"** (24 bars) on dashboard — currently only daily aggregate is visible.

### Phase 3 — cost saver

- [ ] **Image cache / dedup.** Hash uploaded image, return cached result instead of re-paying AI. Caveat: same photo ≠ same dish always (lighting/angle differences). Make opt-in or fuzzy with confidence threshold.

### Phase 4 — proactive alerting

- [ ] **Alert** (Telegram or email) when `error_rate > 10%` over the last hour. Needs SMTP creds or bot chat-id.

---

## v1.1.x — мінорні UI-патчі

- [ ] **Версія в навбарі.** Зараз `app/main.py` тримає `version="2.0.0"` як строку у FastAPI декларації — нікуди не виводиться. Додати в `app/layout.py:nav_html()` рядок `<span class="version">v{__version__}</span>` біля бренду. Источник правди — single constant у `app/__init__.py` або з `pyproject.toml`/git-tag. Кожен реліз — bump.
- [ ] **Default model = `haiku`** (зараз `sonnet`). Встановити `DEFAULT_MODEL=haiku` у `.env` (або у `config.py` як default). Швидке переключення для економії — Haiku 4.5 у ~4x дешевший за Sonnet (~$0.80/M in vs $3, $4/M out vs $15). Перевірити що якість розпізнавання достатня (TBD test pass on existing dataset). При погіршенні — повертаємо Sonnet або вводимо tier-based selection (v1.3) раніше.

---

## v1.2 — Web admin + settings + scale + mobile users

### Mobile user_id + Firebase integration + Users page

- [ ] **`mobile_user_id` колонка у `requests`** (TEXT, бо Firebase UID = 28-символьний string). Mobile-app шле header `X-User-Id: <firebase_uid>` разом з фотографією у multipart POST. Записуємо в БД, прив'язуючи кожен скан до конкретного користувача.
- [ ] **Firebase Admin SDK інтеграція.** Додаємо `firebase-admin` у `requirements.txt`. Service-account JSON кладемо в `data/firebase-service-account.json` (gitignored, шлях у `.env` як `FIREBASE_CRED_PATH`). На старті ініціалізуємо Firebase app. Створюємо `app/firebase.py` з функцією `get_user_profile(uid) -> dict | None` що тягне Auth profile + Firestore document `users/{uid}`. **Поля для маркетингу і per-user стат:** email, displayName, photoURL, gender, age/date_of_birth, country, language, weight_kg/height_cm (якщо BroCalories це збирає при онбордингу), daily_calorie_goal/goal, subscription_tier/expires_at, referral_source, last_active_at, custom_claims. Точний перелік — з мобільним розробником (Q-012). Брифу для них — [`firebase-integration-brief.md`](firebase-integration-brief.md).
- [ ] **Кеш user-data** — щоб не бити Firebase на кожен запит. Локальна таблиця `mobile_users(uid TEXT PRIMARY KEY, email, display_name, photo_url, subscription_status, raw_json TEXT, fetched_at REAL)`. TTL ~24 години. При кожному `/analyze/` запиті перевіряємо: якщо в `mobile_users` нема або застаріле — fetch from Firebase (async, не блокує response), оновлюємо.
- [ ] **Web Users page (`/users`)** — список усіх відомих юзерів (mobile + telegram, об'єднані в одну таблицю з типом). Колонки: avatar/email/display_name (для mobile) або username/handle (для TG), total scans, total cost, last scan date, subscription status. Фільтри: тип (mobile/tg/anon), search by email/name.
- [ ] **User detail page (`/users/<uid>`)** — повна сторінка одного юзера: профіль (Firebase data), статистика (total scans / total cost / avg cost / first scan / last scan), історія сканувань (паджинований список як History, але pre-filtered по цьому user_id), графік активності.
- [ ] **Drill-down з Recent / by-day у дашборді** — клік на user-id → веде на `/users/<uid>`.
- [ ] **Anonymous bucket** — запити без `mobile_user_id` і без `telegram_user_id` згрупувати як "Anonymous (legacy)" для зручності — окремий рядок у Users page що показує загальну кількість і куди вони ходили (поки не оновили додаток).

### Admin Users в БД (з .env→DB міграцією, без втрати доступу)

- [ ] **Нова таблиця** `admin_users(id, email, password_hash, role, status, created_at, last_login)`. Hash через bcrypt (новий dep — `passlib[bcrypt]`).
- [ ] **Backward-compat:** при старті — seed з `.env` (`ADMIN_USERNAME`/`ADMIN_PASSWORD` + `ADMIN_USERS=email:pass,…`). Якщо запис уже в БД — НЕ перезаписуємо. Якщо новий — INSERT з hash. Існуючі користувачі (admin, alexandr.shulga, elena.okhrimovych) автоматично потрапляють у БД при першому деплої — доступ зберігається.
- [ ] **Web-UI Users page** (`/users`) — список email/role/status/last_login, кнопки: Add User (modal з email+password), Disable/Enable, Reset Password. Тільки для роль=`superadmin` (перший з `.env` стає superadmin).
- [ ] `auth.py:verify_credentials()` — спочатку шукає в БД, потім fallback на `.env` (на випадок якщо БД зламана — зберігаємо emergency access).

### Settings page

- [ ] **Нова таблиця** `settings(key TEXT PRIMARY KEY, value TEXT, updated_at REAL, updated_by INTEGER)`.
- [ ] Settings UI (`/settings`) — поля: default provider, default model for bot, fallback chain order, MAX_IMAGE_SIZE_MB, STORE_IMAGES toggle.
- [ ] `config.py` — `get_setting(key, default=...)` спочатку дивиться в БД, потім в `.env`. Hot-reload (читання при кожному запиті — це SQLite, дешево).

### Mandatory token + scale (вже були в roadmap)

- [ ] Mandatory `Authorization: Bearer` на `/analyze/` (фінал v1.1 rollout)
- [ ] Per-user history для mobile (юзер бачить свою у мобільному)
- [ ] PostgreSQL міграція коли SQLite перестане встигати
- [ ] HTTPS на nginx (Certbot)
- [ ] Nightly backups `stats.db` + `images/`

---

## v1.3 — Tier-based model selection (subscription)

### Концепція

Підписочна модель BroCalories: paid юзери → кращі моделі (Sonnet/gpt-4o/pro), free → дешевші (Haiku/mini/flash-lite). Backend підставляє модель автоматично; розробники з прямим API-доступом можуть передати конкретну модель і override-ити.

### Tier→model mapping (концепт)

| Provider | `free` | `paid` |
|---|---|---|
| anthropic | `haiku` (4.5) | `sonnet` (4.6) |
| openai | `gpt4o-mini` | `gpt4o` |
| google | `flash-lite` (2.0) | `flash` (2.0) або `pro` (2.5) |

Mapping тримається в `settings` таблиці — можна міняти через UI без рестарту.

### Items

- [ ] Колонки `tier TEXT DEFAULT 'paid'` у `clients` (per-client tier, наприклад "BroCalories paid pool" vs "BroCalories free pool" — або одна таблиця тримає окремі tokens на різні tier-и).
- [ ] Альтернативно (як буде per-user auth у v1.2): колонка `tier` в `users` (per-user). Більш гранулярно.
- [ ] `/analyze/` логіка:
  - якщо `model` явно передано → використовуємо як є (override для розробників)
  - якщо `model` НЕ передано → підбираємо за `provider + tier` mapping
- [ ] Fallback: підбирає **ту саму tier-модель** з наступного провайдера (free→free, paid→paid). Не зкатуємо paid юзера в free-модель просто бо primary впав.
- [ ] Dashboard: cards "Cost free vs paid", % розподілу.
- [ ] **Backward-compat:** якщо у клієнта `tier=NULL` → поводимось як зараз (default Sonnet). Жодних breaking changes.

---

## Open questions / pre-checks

---

## Open questions / pre-checks

- Verify whether the Anthropic provider already uses prompt caching — affects whether `cache_read_tokens` column is needed.

## Decisions log

- **2026-05-06** — Pricing snapshot policy: `cost_usd` is fixed at request time; we don't rewrite history when prices change.
- **2026-05-06** — Backfill of old records rejected: no tokens stored → can't compute even with today's price.
