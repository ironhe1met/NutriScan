# Discovery Brief — NutriScan

> Brownfield retrospective discovery. Project predates Daedalus pipeline; this brief reverse-engineers state from code + product owner context, not greenfield Q&A.

## 1. Elevator Pitch

> **NutriScan — це AI-сервіс детекції поживних речовин з фото страви, для мобільного додатку BloCalories (Android) та закритого Telegram-боту, який повертає JSON з інгредієнтами, вагою, калоріями і БЖУ через multi-provider AI fallback (Anthropic → OpenAI → Google).**

## 2. Суть проєкту

- **Назва:** NutriScan
- **Тип:** API-сервіс + internal admin (observability)
- **Проблема:** користувачам мобільного calorie-трекера незручно вручну вбивати кожен прийом їжі (виписувати інгредієнти, шукати калорії, рахувати макроси). Хочуть «сфоткав → отримав готовий розклад».
- **Валідація проблеми:** підтверджена — є реальний клієнт (BloCalories у Google Play) і активна продакшн-навантаження (1572 запити в БД станом на 2026-05-06, 1375 успішних, 197 failed).
- **Рішення:** REST API `POST /analyze/` з multi-provider AI fallback (Anthropic Sonnet за замовчанням → OpenAI gpt-4o → Google Gemini). Pydantic-валідований JSON-вихід. Веб-адмінка для observability (dashboard, історія, failed-таб з повними помилками).

## 3. Цільова аудиторія

- **Основна:** користувачі мобільного додатку **BloCalories** (Android, Google Play; Apple App Store не запланований). Технічний рівень — нетехнічні. Кількість — TBD (питання 🔴 Q-001).
- **Вторинна:** учасники закритого Telegram-боту (whitelist через `BOT_ALLOWED_USERS` env var). Призначений для тестування і близького кола. Кількість — десятки максимум.
- **Внутрішня:** оператор/розробник (Євгеній + допущені email-и в `ADMIN_USERS`) — користуються адмін-панеллю для моніторингу, аналізу failed-помилок, контролю провайдерів.

## 4. Ролі та доступ

| Роль | Що може | Як автентифікується |
|------|---------|--------------------|
| **mobile user (BloCalories)** | відправити фото → отримати JSON | поки що БЕЗ auth (HTTP API відкритий) — питання 🔴 Q-002 |
| **TG user (whitelisted)** | відправити фото боту → отримати markdown-відповідь | Telegram user_id у `BOT_ALLOWED_USERS` |
| **admin** | повний доступ до dashboard, history, failed-таб, налаштувань | session-cookie, креди в `.env` (`ADMIN_USERNAME`/`ADMIN_PASSWORD` + `ADMIN_USERS=email:pass,…`) |

- **Multi-tenancy:** ні. Усі запити в одному `requests`-table. Зараз **не привʼязані до користувача** взагалі — нема ні `telegram_user_id`, ні `mobile_user_id`. Це обмежує per-user аналітику і rate-limit. Записано як v1.1 Phase 1 пункт #2.

## 5. Ключові функції (MVP — вже у проді)

- [x] `POST /analyze/` — multipart фото → JSON {dish_name, ingredients[], total} (Pydantic-validated)
- [x] Multi-provider fallback chain (Anthropic → OpenAI → Google)
- [x] Telegram-бот як інтерактивний клієнт (`/start`, `/settings`, photo handler)
- [x] Адмін-панель: Dashboard з date-filter (today/7d/30d/90d/all/custom), Daily breakdown, drill-down
- [x] History з табами Success/Failed, повним текстом помилок (заміна логам у термiналі)
- [x] Збереження зображень на диск (опціонально через `STORE_IMAGES=true`)
- [x] Деплой через `deploy.sh` + systemd (`nutriscan.service`, `nutriscan-bot.service`) + nginx

**Одна головна функція:** `POST /analyze/` з fallback chain. Без неї решта — обгортка.

## 6. Що НЕ входить (свідомо)

- Аутентифікація мобільних клієнтів (BloCalories шле без токена — TBD)
- Per-user статистика / історія (нема user-id у БД)
- Rate-limiting (контроль витрат лише через провайдер-квоти)
- Tests (`tests/` порожня)
- HTTPS на nginx (зараз тільки port 80, без TLS — *обговорено з користувачем 2026-05-06, відкладено*)
- Cost / token tracking (заплановано — v1.1 Phase 1)
- Image dedup / cache (заплановано — v1.1 Phase 3)
- Alerting на error spike (заплановано — v1.1 Phase 4)
- Unit/integration tests
- Prompt caching (Anthropic) — TBD чи використовувати

## 7. Дані та сутності

| Сутність | Обсяг (станом на 2026-05-06) | Ріст | Чутливість |
|----------|------------------------------|------|------------|
| `requests` (один лог-table) | 1572 рядки | ~80-110/день | низька (без PII; зображення страв) |
| `data/images/` (диск) | ~1500 файлів JPG/PNG/WEBP | ~80-110/день | низька |

**Нема:** users-таблиці, sessions у БД (session у cookie, signed `itsdangerous`), окремих agg-таблиць.

**Schema `requests`:** `id`, `timestamp` (REAL unix-ts), `provider`, `model`, `response_time_ms`, `success`, `error`, `dish_name`, `image_size_bytes`, `ingredients_count`, `result_json` (повний JSON), `image_filename`. Auto-міграція додає колонки при старті (`ALTER TABLE … IF NOT EXISTS` semi-pattern через try/except).

**Пошук/фільтрація:** є — за датою (одиничний день, range), за статусом (success/failed), за провайдером/моделлю в by-provider/model звіті.

## 8. Існуючі активи

- **Код:** monorepo `/home/ironhelmet/projects/NutriScan/`, GitHub `ironhe1met/NutriScan`. Останній коміт `8090097`. Гілка `main` чиста.
- **Дизайн/бренд:** мінімальний — slate-dark UI (#0f172a, #1e293b, #38bdf8 акцент) у [layout.py](app/layout.py). BloCalories — окрема торгова марка (Google Play app, не у нашому скоупі по UI).
- **Домен:** `nutriscan.radarme.com.ua` (HTTP only, port 80). Apex `radarme.com.ua` керує Hetzner-сервером Radar-Adm.
- **Сервер/інфра:** прод на `radar-adm` (Hetzner; OS Ubuntu 24.02; SSH `ssh root@radar-adm` без пароля; `e.chernenko` user для людської роботи з sudo). Сервіс лежить у `/opt/NutriScan`. Systemd unit-и `nutriscan.service` + `nutriscan-bot.service`.
- **Дані для міграції:** немає (новий проєкт без legacy-даних). Поточна БД `data/stats.db` — джерело правди, бекапів окремих не налаштовано (питання 🟡 Q-006).

## 9. Інтеграції

| Сервіс | Навіщо | Auth | Rate limits | Формат | Надійність |
|--------|--------|------|-------------|--------|------------|
| **Anthropic API** | основний AI provider (Claude Sonnet 4.6 default; +Opus 4.6, Haiku 4.5) | API key (`ANTHROPIC_API_KEY`) | tier-based, не моніторимо | JSON через SDK `AsyncAnthropic` | fallback → OpenAI |
| **OpenAI API** | fallback провайдер (gpt-4o, gpt-4o-mini) | API key (`OPENAI_API_KEY`) | tier-based | JSON через `AsyncOpenAI` | fallback → Google |
| **Google Gemini API** | second fallback (gemini-2.0-flash, flash-lite, 2.5-pro-preview) | API key (`GOOGLE_API_KEY`) | tier-based | JSON через `google.genai.Client` | last in chain |
| **Telegram Bot API** | інтерфейс для тестових/закритих користувачів | bot token (`BOT_TOKEN`) | TG default | aiogram v3 | бот-сервіс окремий systemd unit |

**Fallback chain:** `FALLBACK_PROVIDERS=anthropic,openai,google` (env). Якщо primary падає — пробуємо наступний; в response headers `X-Fallback-From`, `X-Attempts` для діагностики. **Caveat:** при fallback використовується default-модель наступного провайдера, не оригінальна модель користувача.

## 10. Платформа та deployment

- **Платформа:** API (HTTP REST) + admin web + Telegram bot
- **Deployment:** один сервер `radar-adm` (Hetzner, dedicated). Без Docker, без Kubernetes — pip-venv + systemd + nginx. Ubuntu 24.02.
- **Обмеження:** 
  - nginx upload max 12 MB (бо food photos бувають великі)
  - app max image 10 MB (`MAX_IMAGE_SIZE_MB`)
  - uvicorn слухає тільки 127.0.0.1:8000, nginx проксує
  - HTTP only (без TLS — на потім)

## 11. Конкуренти та аналоги

| Аналог | Сильні сторони | Слабкі сторони | Чим ми краще |
|--------|---------------|----------------|--------------|
| MyFitnessPal scan | велика база, інтеграції | потребує barcode/штучне введення | автоматичне розпізнавання з фото без штрихкоду |
| Calorie Mama AI | такий самий концепт photo→nutrition | пропрієтарний, нема API для third-party апп | відкритий API для нашого BloCalories |
| Bite AI / Foodvisor | mobile-first, добра ML | закриті екосистеми | контроль над промптом, fallback на 3 провайдери |

(*Цю таблицю PRD-агент може уточнити деталями; зараз — поверхневий контекст.*)

## 12. Мови та локалізація

- **Основна:** інтерфейс адмінки — англійська (label-и в layout.py / dashboard / history).
- **Промпт до AI:** англомовний (`SYSTEM_PROMPT` у `app/prompt.py`).
- **Output JSON:** `dish_name`, `name` інгредієнтів — англійською (бо AI генерує англ; страви на укр/рос фотках теж описує англ).
- **Telegram bot:** повідомлення англомовні (комбінуються з AI-output).
- **i18n:** не реалізовано і не запланований (TG-бот для близького кола; BloCalories має власну локалізацію на mobile-стороні).

## 13. Монетизація

- **Поточна модель:** немає прямої монетизації NutriScan. Це backend-сервіс для BloCalories (мобільний додаток). Монетизація — на стороні мобільного.
- **Cost-side:** платимо AI-провайдерам за виклики (Anthropic Sonnet ~$3/M in, $15/M out + інші). Зараз **не вимірюємо** — питання плану на v1.1.

## 14. Дедлайни та ризики

- **Хард-дедлайн:** немає.
- **Припущення:** 
  - prod-навантаження залишається в межах ~100 запитів/день найближчий квартал
  - SQLite витримає (стиснений 1572-row dataset = декілька MB)
  - провайдери AI не змінять контракти різко (хоч моделі переіменовуються — fallback chain дає страховку)
- **Ризики:**
  - 🔴 нема auth у `POST /analyze/` — публічний ендпоінт, хто завгодно з URL може спалювати наші AI-кредіти. Прихована вузька публікою (нема SEO), але в principle відкрита.
  - 🟡 нема alerting на сплеск помилок — failed/спам можемо помітити лиш у дашборді post-factum
  - 🟡 нема бекапів `data/stats.db` (питання 🟡 Q-006)
  - 🟡 SQLite blocks при паралельних writes (зараз ОК, але 1000+/день з кількох клієнтів — треба буде PostgreSQL)
  - ⚪ HTTP-only adminка з кредами — теоретично перехопити на WiFi-кафе. Поки adminку юзає тільки оператор з відомих мереж — терпимо. На потім — TLS.
- **Регуляторні вимоги:** немає (food data ≠ медичні дані; нема PII). GDPR не торкається бо нема user-tracking.

## 15. Метрики успіху

- **Технічні:**
  - Success rate ≥ 95% (зараз ~96.2% за останні 7 днів)
  - Avg response time ≤ 25 секунд (зараз ~20 с для Sonnet)
  - Failed-таб дозволяє діагностувати без `ssh` у термінал (зроблено в v1.0.x)
- **Продуктові (для v1.1):**
  - cost / day знаходиться в дашборді (планується)
  - cost / користувач — після впровадження user-id (планується)
- **Бізнес:** залежать від BloCalories — поза скоупом backend-проєкту.

## 16. Roadmap (скелет)

| Версія | Що входить | Done коли | Статус |
|--------|-----------|-----------|--------|
| **v1.0** | Photo → JSON, multi-provider fallback, TG-бот, admin login | вже у проді | ✅ released |
| **v1.0.x** | Dashboard date-filter + daily breakdown; History tabs Success/Failed з повним error-текстом | 2026-05-06 | ✅ released |
| **v1.1** | Tokens + cost stats (Phase 1) → per-user (TG user_id) → CSV export → hourly chart → image-cache → alerting | TBD | 🟡 planned (див. `ideas.md`) |
| **v1.2** | BloCalories auth + per-user history; PostgreSQL міграція; HTTPS на nginx | TBD | ⏳ будь-коли після v1.1 |
| **v2.0** | (TBD) — можлива інтеграція з MyFitnessPal/Apple Health/Google Fit | open | ⏳ |

(детально по v1.1 — у [`ideas.md`](ideas.md))

## 17. Схожі проєкти

- **P-0009 — AI Members Agent** (Wemates antifraud): теж FastAPI + AI-провайдер + admin web. Перевикористати: фактично однакова архітектура (FastAPI + admin), можна позичити підходи до RBAC коли буде user-auth.
- **P-0006 — DataPIM**: AI-збагачення PIM, теж GPT-4 vision. Перевикористати: досвід з vision-промптами.
- Інших food/calorie-проєктів у registry немає.

---

## Handoff → наступний агент

- **Pipeline:** `app` (вже встановлено в Daedalus DB; admin-web частина важлива, тому не `api`)
- **Складність:** Medium — 3 AI-провайдери, 2 типи клієнтів (mobile, TG), web admin, але одна таблиця БД, один сервер, без RBAC.
- **Фактори:** **немає** PII (Security НЕ обовʼязковий), **немає** перформанс-NFR (Performance відкласти до v1.2 коли підемо на PostgreSQL), **є** file uploads (зображення — варто чекнути в Security якщо буде), **немає** background jobs.
- **Наступний агент:** `prd` (по таблиці app pipeline → prd).
- **Головний фокус для PRD:** зафіксувати use-cases для BloCalories (mobile-side контракт), для TG-бота (whitelist policies, settings persistence), для admin observability (дашборд як заміна логам).
- **Ключові ролі:** mobile_user (без auth — RED), tg_user (whitelist), admin (session-based)
- **Ключові сутності:** `requests` (єдина таблиця-лог), `images` (на диску)
- **Ключові інтеграції:** Anthropic / OpenAI / Google API (з fallback), Telegram Bot API
- **Red flags:**
  - Public `POST /analyze/` без auth — burn-through ризик кредитів
  - Bot user_prefs у пам'яті — губляться при рестарті
  - Зміни моделі при fallback — користувач хотів `pro`, отримав `flash`
  - Жодних tests
- **Складні місця:** image dedup (Phase 3) — fuzzy logic, false positives
- **Відкриті питання:** 6 у `questions.md` (2 🔴, 3 🟡, 1 ⚪)
- **Обмеження:** один сервер, без Docker, SQLite — для всіх архітектурних рішень мають значення
- **Дедлайн:** немає
