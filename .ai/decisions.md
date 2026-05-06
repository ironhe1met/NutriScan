# NutriScan — Architectural Decisions Log

DEC-NNN — формальні архітектурні рішення (зворотний chronological log). Деталі чому/як зафіксовано в `resolved.md`. Тут — короткий перелік для швидкого огляду.

---

## DEC-001 — SQLite as primary store (v1.0)

**Decision:** Використовуємо SQLite (`data/stats.db`) як єдину БД для логування запитів і прав адмін-доступу.
**Trade-off:** Нема concurrent writes, нема реплікації, бекап = file copy. Достатньо для one-server, low-write workload.
**Trigger to revisit:** > 5 пишучих процесів або > 10K запитів/день.

## DEC-002 — Multi-provider AI fallback chain

**Decision:** Anthropic → OpenAI → Google як послідовність fallback (env `FALLBACK_PROVIDERS`).
**Trade-off:** Кожен fallback використовує свою default-модель (не відображає вибір користувача — див. Q-005). Виграш — стійкість при простоях провайдерів.

## DEC-003 — Admin auth via session cookie + .env credentials

**Decision:** Адмін-користувачі визначаються в `.env` (`ADMIN_USERNAME`/`ADMIN_PASSWORD` + `ADMIN_USERS=email:pass,…`), сесія підписана `itsdangerous`.
**Trade-off:** Нема ротації паролів через UI, нема SSO. Достатньо для команди < 10 осіб.

## DEC-004 — No auth on `POST /analyze/` (v1.0, провизорно)

**Decision:** Публічний ендпоінт без auth — клієнти (BloCalories, TG-bot) шлють напряму.
**Trade-off:** Хто завгодно з URL може споживати наші AI-кредити (security through obscurity). Прийнятно поки нема публічного marketing-у; v1.2 закриває (Q-002).

## DEC-005 — Cost snapshot at request time (v1.1)

**Decision:** `cost_usd` фіксується в БД при INSERT і не перераховується при зміні прайсів.
**Trade-off:** Аналітика собівартості стабільна; неможливо retroactively показати "якби тоді був інший прайс".
**Reference:** R-001 у `resolved.md`.

## DEC-006 — Pipeline class = `app` (Daedalus retro-classification)

**Decision:** Незважаючи на API-first ядро, класифікуємо проєкт як `app` через активний admin web-component з UX-логікою (фільтри, дашборд, drill-down).
**Trade-off:** Pipeline `app` тягне design + frontend-skeleton як етапи; для NutriScan вони "light" (admin = HTML-strings у layout.py, не SPA).
**Reference:** R-003 у `resolved.md`.
