# NutriScan — Ideas / Roadmap

## v1.1 — observability + UX bundle

Recommended order. Each phase = one PR.

### Phase 1 — DB migration (one PR)

- [ ] **Tokens + cost stats.** Add columns `input_tokens`, `output_tokens`, `cost_usd` to `requests`. **Snapshot at request time** (not on-the-fly) — history doesn't get rewritten when prices change. Pricing dict per `(provider, model)` in `config.py`. If we already use Anthropic prompt caching — add `cache_read_tokens` column. **UI:** new dashboard cards (Total tokens, Total cost, Avg $/req, Cost/day), columns in By Provider/Model and By Day, `≈$` in History detail. **Old 1572 records:** leave as `—` (no token data → can't even compute with today's price).
- [ ] **Per-user stats (Telegram).** Add `telegram_user_id` column to `requests`. Without it we can't see who burns budget or rate-limit per user.

### Phase 2 — UI on top of new data

- [ ] **CSV export** buttons on History/Failed (bookkeeping, audits).
- [ ] **Hourly chart for "today"** (24 bars) on dashboard — currently only daily aggregate is visible.

### Phase 3 — cost saver

- [ ] **Image cache / dedup.** Hash uploaded image, return cached result instead of re-paying AI. Caveat: same photo ≠ same dish always (lighting/angle differences). Make opt-in or fuzzy with confidence threshold.

### Phase 4 — proactive alerting

- [ ] **Alert** (Telegram or email) when `error_rate > 10%` over the last hour. Needs SMTP creds or bot chat-id.

---

## Open questions / pre-checks

- Verify whether the Anthropic provider already uses prompt caching — affects whether `cache_read_tokens` column is needed.

## Decisions log

- **2026-05-06** — Pricing snapshot policy: `cost_usd` is fixed at request time; we don't rewrite history when prices change.
- **2026-05-06** — Backfill of old records rejected: no tokens stored → can't compute even with today's price.
