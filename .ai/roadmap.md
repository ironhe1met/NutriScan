# NutriScan — Roadmap

## Поточна версія: v1.0.x (production)

Сервіс у проді на `nutriscan.radarme.com.ua` (Radar-Adm, Hetzner). 1572 запитів у БД станом на 2026-05-06; success rate 96.2%.

## Версії

| Версія | Що входить | Done коли | Статус |
|--------|-----------|-----------|--------|
| **v1.0** | Photo → JSON, multi-provider fallback (Anthropic/OpenAI/Google), TG-бот, admin login | до 2026-05-06 | ✅ released |
| **v1.0.x** | Dashboard date-filter + daily breakdown; History tabs Success/Failed з drill-down і повним error-текстом | 2026-05-06 | ✅ released (commit `f5e6ecd`, `8090097`) |
| **v1.1** | Observability + UX bundle (4 фази, див. нижче) | TBD | 🟡 planned |
| **v1.2** | Mobile auth + per-user history; PostgreSQL міграція; HTTPS на nginx | TBD | ⏳ candidate |
| **v2.0** | Інтеграція з MyFitnessPal / Apple Health / Google Fit | TBD | ⏳ ідея |

---

## Деталі по версіях

### v1.0.x — у проді

**Мета:** робочий API + закритий TG-бот + працююча admin observability.

| Компонент | Статус |
|-----------|--------|
| `POST /analyze/` (multipart, multi-provider) | ✅ |
| Anthropic/OpenAI/Google providers + fallback chain | ✅ |
| TG bot з `/start`, `/settings`, photo handler | ✅ |
| Admin: dashboard з фільтрами, history з табами Success/Failed | ✅ |
| Failed-таб з expandable error-text (заміна логам) | ✅ |
| Image storage (опціонально) + history detail view | ✅ |
| systemd + nginx деплой через `deploy.sh` | ✅ |

---

### v1.1 — observability + UX bundle (planned)

**Мета:** бачити скільки коштують AI-виклики, хто їх робить, не лазити в термінал по статистику, не платити двічі за ту саму фотку.

Фазована (кожна фаза = окремий PR). Деталі — у [`ideas.md`](ideas.md).

| Phase | Компонент | Статус |
|-------|-----------|--------|
| 1 | Tokens + cost stats (БД-міграція + UI) | ✅ released 2026-05-06 (`56f9a26`) |
| 1 | API-token auth на `/analyze/` — **Phase A: Optional** (anon allowed, valid token tagged) | ✅ released 2026-05-06 |
| 1 | API-token auth — **Phase B: Wait** for Google Play rollout (~1-2 тижні) | 🟡 in progress (BroCalories token created, чекаємо моб-реліз) |
| 1 | API-token auth — **Phase C: Mandatory** (no token → 401) | ⏳ pending (after Phase B) |
| 1 | Per-user stats (`telegram_user_id` колонка) | ✅ released 2026-05-06 |
| 2 | CSV export для History/Failed | ⏳ pending |
| 2 | Hourly chart "today" (24 bars на дашборді) | ⏳ pending |
| 3 | Image-cache / dedup (хеш-based, opt-in) | ⏳ pending |
| 4 | Alerting (TG/email при error_rate > 10%/год) | ⏳ pending |

**Pre-checks для Phase 1:**
- Чи Anthropic provider використовує prompt caching? (впливає на потребу `cache_read_tokens` колонки)

---

### v1.1.x — мінорні UI-патчі (швидкі)

| Компонент | Статус |
|-----------|--------|
| Версія NutriScan видна в навбарі (наприклад `NutriScan v2.0.0`) | ⏳ |
| Footer з посиланням на GitHub repo | ⏳ optional |

---

### v1.2 — Web admin + settings + scale (candidate)

**Мета:** управління адмін-юзерами через web (без правки `.env`), Settings page для дефолтів, scale за межі SQLite.

| Компонент | Статус |
|-----------|--------|
| **Admin Users у БД** — нова таблиця `admin_users(id, email, password_hash, role, status, created_at)`. Web-UI (Users page): список, додати, видалити, скинути пароль. Backward-compat: `.env` залишається працювати як seed/fallback (мігруємо існуючих email-ів — `admin/xvviimcmxc`, `alexandr.shulga@radarme.com`, `elena.okhrimovych@radarme.com` — щоб ніхто не втратив доступ). Окремий DEC + R-NNN. | ⏳ |
| **Settings page** — UI для конфігу (default provider, default model для бота, fallback chain, MAX_IMAGE_SIZE_MB). Збереження в нову таблицю `settings(key, value, updated_at, updated_by)`. Hot-reload без рестарту. | ⏳ |
| **Mandatory token** на `/analyze/` (фінал rollout-у v1.1) | ⏳ |
| Per-user history для mobile (юзер бачить свою) | ⏳ |
| **PostgreSQL** міграція з SQLite | ⏳ trigger: >1000 req/day або >5 пишучих процесів |
| **HTTPS на nginx** (Certbot) | ⏳ |
| Backups `data/stats.db` + `data/images/` | ⏳ |
| Apple App Store випуск BroCalories | ❓ external |

---

### v1.3 — Tier-based model selection (subscription)

**Мета:** підписочна модель для BroCalories — paid юзери отримують кращі моделі, free → дешевші.

**Концепція:** клієнтам (або per-user в межах клієнта) призначається tier (`free` / `paid`). Backend сам обирає модель з провайдера за tier-mapping:

| Provider | `free` модель | `paid` модель |
|---|---|---|
| anthropic | `haiku` | `sonnet` |
| openai | `gpt4o-mini` | `gpt4o` |
| google | `flash-lite` | `flash` (або `pro` для preview) |

| Компонент | Статус |
|-----------|--------|
| Колонки `tier` (free/paid) у `clients` (per-client) і `users` (per-user — для майбутньої BroCalories per-user auth) | ⏳ |
| Tier→model mapping config у БД (Settings table) — щоб міняти без рестарту | ⏳ |
| `/analyze/` — якщо клієнт не передає `model`, обираємо за tier. Якщо передає — лишаємо як override (для розробників/тестування). | ⏳ |
| Fallback: при fail primary провайдера — підбираємо ту саму tier-модель з наступного провайдера. | ⏳ |
| Dashboard: cost per tier, % free vs paid | ⏳ |
| **Backward-compat:** дефолтна логіка (без tier у клієнта) працює як зараз — Sonnet | ⏳ |

---

### v2.0 — далеко

**Мета:** інтеграції з третіми сторонами.

| Компонент | Статус |
|-----------|--------|
| MyFitnessPal sync | ⏳ ідея |
| Apple Health export | ⏳ ідея |
| Google Fit export | ⏳ ідея |
