# NutriScan — Pipeline Status

**Project:** NutriScan (P-0007)
**Pipeline:** `app`
**Current version (production):** v1.0.x
**Repo:** [github.com/ironhe1met/NutriScan](https://github.com/ironhe1met/NutriScan)
**Production URL:** http://nutriscan.radarme.com.ua/
**Production server:** Radar-Adm (Hetzner) — `ssh root@radar-adm`, app у `/opt/NutriScan`

---

## Pipeline stages

| Stage | Status | Artifact | Updated |
|-------|--------|----------|---------|
| **discovery** | ✅ done (retro) | [`discovery.md`](discovery.md) | 2026-05-06 |
| **prd** | ⏳ pending | — | — |
| **architect** | ⏳ pending | — | — |
| **design** | ⏳ optional (admin only — light) | — | — |
| **frontend-skeleton** | ⏳ skip (no separate frontend) | — | — |
| **developer** | ✅ done (code exists in repo, audited) | (existing code) | ongoing |
| **qa** | ❌ NOT done (`tests/` empty) | — | — |
| **performance** | ⏳ defer to v1.2 (PostgreSQL migration) | — | — |
| **security** | ⏳ blocked by Q-002 (auth strategy for mobile) | — | — |
| **devops** | ✅ done (deploy.sh, systemd, nginx — working) | implicit | ongoing |
| **iteration** | 🟡 active (v1.1 planned) | [`ideas.md`](ideas.md), [`roadmap.md`](roadmap.md) | 2026-05-06 |

---

## Next actions

1. **product owner** — ревью `discovery.md` + відповіді на 🔴 питання у [`questions.md`](questions.md) (Q-001 кількість юзерів, Q-002 mobile auth).
2. **Then** → запустити `/agent prd` для формалізації user stories і AC v1.1.
3. **Then** → `/agent architect` (вирішити: SQLite чи PG для v1.2; cache_read_tokens колонка; auth pattern для mobile).
4. **Parallel** → можна одразу йти у v1.1 Phase 1 implementation (tokens/cost) бо це incremental, не блокується PRD.

---

## Open blockers

- 🔴 Q-002: auth для mobile-клієнтів — без нього `POST /analyze/` лишається відкритим.
- 🔴 Q-001: реальна кількість користувачів — без цього не зрозуміло коли triggerити PG-міграцію.

---

## Recent activity

- 2026-05-06 — v1.1 Phase 1 deployed (tokens+cost, optional Bearer, per-user TG, clients table)
- 2026-05-06 — prod API-token created for BroCalories (id=1) — awaiting mobile app release

- 2026-05-06 — nginx rate-limit на /analyze/ (30/min per IP, burst 10) — applied + verified
- 2026-05-06 — name corrected: BloCalories → BroCalories (in .ai/ + Daedalus DB)

- 2026-05-06 — discovery (retro) + roadmap + ideas v1.1 — recorded
- 2026-05-06 — v1.0.x: Failed-tab з error-text, dashboard date-filter, by-day breakdown — released
- 2026-05-06 — admin user `elena.okhrimovych@radarme.com` додано в production
