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
| 1 | Tokens + cost stats (БД-міграція + UI cards/columns) | ⏳ pending |
| 1 | Per-user stats (`telegram_user_id` колонка) | ⏳ pending |
| 2 | CSV export для History/Failed | ⏳ pending |
| 2 | Hourly chart "today" (24 bars на дашборді) | ⏳ pending |
| 3 | Image-cache / dedup (хеш-based, opt-in) | ⏳ pending |
| 4 | Alerting (TG/email при error_rate > 10%/год) | ⏳ pending |

**Pre-checks для Phase 1:**
- Чи Anthropic provider використовує prompt caching? (впливає на потребу `cache_read_tokens` колонки)

---

### v1.2 — кандидат

**Мета:** auth для mobile-клієнтів і scale за межі SQLite.

| Компонент | Статус |
|-----------|--------|
| Auth для BroCalories (token-based?) | ⏳ |
| Per-user history (на основі mobile user_id) | ⏳ |
| Міграція SQLite → PostgreSQL (коли write-throughput полізе) | ⏳ |
| HTTPS на nginx (Certbot) | ⏳ |
| Apple App Store випуск BroCalories | ❓ зовнішній фактор |

---

### v2.0 — далеко

**Мета:** інтеграції з третіми сторонами.

| Компонент | Статус |
|-----------|--------|
| MyFitnessPal sync | ⏳ ідея |
| Apple Health export | ⏳ ідея |
| Google Fit export | ⏳ ідея |
