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
**Чому:** Adminку юзає тільки оператор з відомих мереж; mobile-інтеграції BloCalories теж по HTTP поки. Вирішимо разом з v1.2.
**Хто прийняв:** product owner.

## R-007: BloCalories — Android only поки що

**Дата:** 2026-05-06
**Питання:** Apple App Store?
**Рішення:** Тільки Google Play, Apple не у планах поки що.
**Хто прийняв:** product owner.

## R-008: Telegram bot — whitelist-only

**Дата:** 2026-05-06 (фактично давніше, формалізовано)
**Питання:** Чи відкривати TG-бота для всіх?
**Рішення:** **Whitelist** через `BOT_ALLOWED_USERS` у `.env`.
**Чому:** Бот для тестування і близького кола, не для масового продукту. Mass-product — це BloCalories.
**Хто прийняв:** product owner.
