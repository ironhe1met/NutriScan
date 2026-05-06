"""AI provider pricing per 1M tokens (USD).

Snapshotted at request time (R-001) — when prices change, history is NOT rewritten.
Update this dict when providers announce new prices; old records keep their `cost_usd` as-is.

Sources:
- Anthropic: https://www.anthropic.com/pricing  (rates per 1M input/output tokens)
- OpenAI:   https://openai.com/api/pricing
- Google:   https://ai.google.dev/pricing  (Gemini)

Last updated: 2026-05-06.
"""
from __future__ import annotations

# Per 1M tokens. cache_read = 10x cheaper than input for Anthropic prompt caching.
PRICING: dict[tuple[str, str], dict[str, float]] = {
    # Anthropic (Claude 4.x family)
    ("anthropic", "claude-opus-4-6"):           {"input": 15.00, "output": 75.00, "cache_read": 1.50},
    ("anthropic", "claude-sonnet-4-6"):         {"input":  3.00, "output": 15.00, "cache_read": 0.30},
    ("anthropic", "claude-haiku-4-5-20251001"): {"input":  0.80, "output":  4.00, "cache_read": 0.08},

    # OpenAI
    ("openai", "gpt-4o"):      {"input": 2.50, "output": 10.00},
    ("openai", "gpt-4o-mini"): {"input": 0.15, "output":  0.60},

    # Google Gemini
    ("google", "gemini-2.0-flash"):              {"input": 0.075,  "output":  0.30},
    ("google", "gemini-2.0-flash-lite"):         {"input": 0.0375, "output":  0.15},
    ("google", "gemini-2.5-pro-preview-05-06"):  {"input": 1.25,   "output": 10.00},
}


def compute_cost(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    cache_read_tokens: int = 0,
) -> float | None:
    """Returns cost in USD or None if (provider, model) is not in PRICING.

    Anthropic cache_read is billed at the cheaper rate; the rest of input_tokens uses 'input' rate.
    For non-Anthropic providers cache_read_tokens is ignored.
    """
    rates = PRICING.get((provider, model))
    if not rates:
        return None

    fresh_input = max(input_tokens - cache_read_tokens, 0)
    cost = (
        fresh_input / 1_000_000 * rates["input"]
        + output_tokens / 1_000_000 * rates["output"]
        + cache_read_tokens / 1_000_000 * rates.get("cache_read", rates["input"])
    )
    return round(cost, 6)
