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
