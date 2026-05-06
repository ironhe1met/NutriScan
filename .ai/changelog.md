# NutriScan — Changelog (project-level)

Записи про зміни на рівні pipeline / discovery / roadmap. Технічний CHANGELOG для коду — окремо у `CHANGELOG.md` у корені (TBD: створити в v1.1).

---

## 2026-05-06 — Daedalus integration (retro-discovery)

- ✅ Discovery brief написаний на основі існуючого коду + контексту з product owner.
- ✅ `.ai/` структура заповнена: discovery, roadmap, questions, resolved, status, decisions, problems, ideas (вже існував).
- ✅ Pipeline класифіковано як `app` (DEC-006).
- ✅ v1.1 roadmap зафіксований у [`ideas.md`](ideas.md) і [`roadmap.md`](roadmap.md).

## 2026-05-06 — v1.0.x release (admin observability bundle)

- ✅ Dashboard date-filter (today/7d/30d/90d/all + custom range)
- ✅ Daily breakdown з drill-down у History
- ✅ History tabs Success | Failed з повним error-text
- ✅ Failed-pill у by-day, ERR-link у Recent
- Commits: `fb6f644`, `f5e6ecd`, `8090097`

## 2026-05-06 — admin user added

- elena.okhrimovych@radarme.com додано в `ADMIN_USERS` на проді.

## 2026-05-06 — Security hardening + naming fix

- ✅ Mobile client name corrected: BloCalories → BroCalories (8 files in .ai/, Daedalus DB)
- ✅ nginx rate-limit applied on `POST /analyze/`: 30/min per IP, burst 10, max 5 concurrent. HTTP 429 on excess. Verified with 50-parallel test.
- ✅ nginx debug log_format `analyze_debug` enabled (logs auth/api-key/app-id headers) — confirmed mobile sends NO auth headers (R-009).

## 2026-05-06 — v1.1 Phase 1 deployed

- ✅ DB migration: `requests` += {input_tokens, output_tokens, cache_read_tokens, cost_usd, client_id, telegram_user_id}; new `clients` table.
- ✅ `app/pricing.py` — PRICING dict per (provider, model) + `compute_cost()`. Snapshot at request time (R-001).
- ✅ Providers (Anthropic / OpenAI / Google) повертають `(text, usage)` із input/output/cache токенами.
- ✅ `analyze.py` — Optional Bearer token → `client_id` (sha256 lookup); `X-Telegram-User-Id` header. Phase-1 rollout: anon allowed (R-011, DEC-007).
- ✅ TG бот шле `Authorization: Bearer $BOT_API_TOKEN` (опційно) + `X-Telegram-User-Id`.
- ✅ `scripts/manage_clients.py` — CLI add/list/disable/enable + secure token generation (показ один раз).
- ✅ Dashboard: 5 нових карток (Total cost, Cost/day, Avg $/req, Total tokens, Anon %); колонки Tokens+Cost у by-day і by-provider.
- ✅ History list: колонка `≈$`. Detail page: tokens + cost + client_id + tg_user.
- ✅ Prod token для BroCalories згенеровано (id=1) — чекаємо реліз нової версії додатку.
- Коміт: `56f9a26`. Deploy: deploy.sh.


## 2026-05-06 — Roadmap expanded (v1.1.x, v1.2 web admin/settings, v1.3 tier-based)

- ✅ Added v1.1.x patches: NutriScan version visible in navbar.
- ✅ Added v1.2 scope: Web Users page (admin_users table + .env→DB migration with backward-compat); Settings page (default model, provider, MAX_IMAGE_SIZE, hot-reload).
- ✅ Added v1.3 scope: Tier-based model selection (free → cheaper model, paid → premium per provider) with mapping config in DB and override-via-explicit-`?model=` for developers. Backward-compat preserved.
- ✅ New questions Q-009..Q-011 (tier source, .env→DB authority, fallback tier policy).
- ✅ Bugfix to v1.1 Phase 1 (`87e5000`): `get_history`/`get_entry` SELECT now include cost/tokens — `≈$` column shows real values.
