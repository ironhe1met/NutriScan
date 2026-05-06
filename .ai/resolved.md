# NutriScan — Resolved Decisions

Архів питань, які вже були вирішені у розмові з product owner. Агенти читають це перш ніж пере-вирішувати.

---

## R-001: Pricing snapshot policy для tokens/cost (v1.1 Phase 1)

**Дата:** 2026-05-06
**Питання:** Як рахувати `cost_usd` — snapshot у БД на момент запиту чи on-the-fly з поточного прайсу?
**Рішення:** **Snapshot at request time.** Колонка `cost_usd` фіксується при INSERT і ніколи не перераховується.
**Чому:** Прайси AI-провайдерів змінюються; перерахунок «переписав би історію». Аналітика собівартості повинна бути стабільною.
**Хто прийняв:** product owner (Євгеній).

## R-002: Backfill старих 1572 записів — REJECTED

**Дата:** 2026-05-06
**Питання:** Чи дорахувати `cost_usd` для старих записів (до v1.1) хоча б за сьогоднішнім прайсом?
**Рішення:** **Ні.** Старі записи лишаються з `cost_usd = NULL` (відображаються як `—`).
**Чому:** У старих записах немає `input_tokens`/`output_tokens` у БД — рахувати не з чого. Estimate з image_size + ingredients_count = вигадка з помилкою ±50%.
**Хто прийняв:** product owner.

## R-003: Pipeline класифікація — `app`

**Дата:** 2026-05-06
**Питання:** Який Daedalus pipeline для NutriScan — `app` чи `api`?
**Рішення:** **`app`** (вже стояв у DB — лишаємо).
**Чому:** Хоч ядро = API, є web admin-панель з UX-критеріями (фільтри, drill-down, dashboard). Pipeline `app` дає design + frontend-skeleton як опціонально-світлі.
**Хто прийняв:** product owner.

## R-004: Roadmap локально, у репо

**Дата:** 2026-05-06
**Питання:** Де тримати roadmap і ідеї?
**Рішення:** У `<project>/.ai/` файлах (`roadmap.md`, `ideas.md`), коммітити в git разом з кодом.
**Чому:** Стандартна практика Daedalus brownfield-інтеграції: один source of truth поряд з кодом.
**Хто прийняв:** product owner.

## R-005: Failed-таб як заміна логам у термiналі

**Дата:** 2026-05-06
**Питання:** Як показувати failed-запити — окрема сторінка чи tab у History?
**Рішення:** **Tab у History** (Success | Failed) з повним error-text у `<details>` (summary + scrollable monospace pre).
**Чому:** Оператор не повинен ssh-итись на сервер і робити `journalctl -u nutriscan` для розбору AI-помилок. Все має бути у браузері.
**Хто прийняв:** product owner. Реалізовано у v1.0.x (commit `f5e6ecd`).

## R-006: HTTPS на проді — відкладено

**Дата:** 2026-05-06
**Питання:** Накатити Let's Encrypt на nginx?
**Рішення:** **Відкладено** (не зараз).
**Чому:** Adminку юзає тільки оператор з відомих мереж; mobile-інтеграції BroCalories теж по HTTP поки. Вирішимо разом з v1.2.
**Хто прийняв:** product owner.

## R-007: BroCalories — Android only поки що

**Дата:** 2026-05-06
**Питання:** Apple App Store?
**Рішення:** Тільки Google Play, Apple не у планах поки що.
**Хто прийняв:** product owner.

## R-008: Telegram bot — whitelist-only

**Дата:** 2026-05-06 (фактично давніше, формалізовано)
**Питання:** Чи відкривати TG-бота для всіх?
**Рішення:** **Whitelist** через `BOT_ALLOWED_USERS` у `.env`.
**Чому:** Бот для тестування і близького кола, не для масового продукту. Mass-product — це BroCalories.
**Хто прийняв:** product owner.

## R-009: Mobile-app не шле жодних auth headers

**Дата:** 2026-05-06
**Питання:** Чи реально BroCalories шле якийсь токен / API-key / X-User-Id який ми ігноруємо?
**Перевірка:** Розширили nginx `log_format analyze_debug` для `POST /analyze/` — додали `$http_authorization`, `$http_x_api_key`, `$http_x_app_id`, `$http_x_app_version`, `$http_x_user_id`, `$http_x_request_id`. Захоплено живий запит:
```
ua="Dart/3.10 (dart:io)"  auth="-"  xapikey="-"  appid="-"  userid="-"
ctype="multipart/form-data"  len=20197  status=200
```
**Висновок:** **Жодного auth header.** Голий multipart POST. Захист треба додавати з нуля у v1.1 (per-client API-key).

## R-010: Rate-limit на `/analyze/` (stop-gap до v1.1 API-key)

**Дата:** 2026-05-06
**Питання:** Що накатити негайно як захист від зловживань на відкритому `/analyze/`?
**Рішення:** nginx-level rate-limit:
- 30 req/min per IP, burst 10 (короткий сплеск ОК), `nodelay`
- Max 5 одночасних з'єднань per IP
- Перевищення → HTTP 429 + `Retry-After: 60`
- Зони описані в `/etc/nginx/conf.d/nutriscan-ratelimit.conf`, location у `/etc/nginx/sites-enabled/nutriscan.conf`
**Чому:**
- Реальні мобільні юзери — 3-5 запитів/IP/добу, ліміт ніяк не зачіпає
- TG-бот ходить через `127.0.0.1` (минаючи nginx) — теж не зачіпається
- Daily cap відкладено: nginx без redis/memcached не вміє довгі вікна. Денний обмежувач буде в v1.1 разом з per-client API-keys у БД
**Verified:** 50 паралельних POST з одного IP → 45 отримали 429, error.log: `limiting requests, excess: 10.958 by zone "analyze_rl"`.
**Хто прийняв:** product owner.
