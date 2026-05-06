from datetime import datetime, timedelta

PRESETS = [
    ("today", "Today", 1),
    ("7d", "Last 7 days", 7),
    ("30d", "Last 30 days", 30),
    ("90d", "Last 90 days", 90),
    ("all", "All time", None),
]


def parse_iso_date(value: str | None):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value).replace(hour=0, minute=0, second=0, microsecond=0)
    except ValueError:
        return None


def resolve_range(
    preset: str | None,
    date_from: str | None,
    date_to: str | None,
) -> tuple[float | None, float | None, str, str, str]:
    """Returns (from_ts, to_ts, active_preset, from_iso, to_iso).

    Custom range (date_from/date_to) wins over preset. Default preset = 30d.
    `to` is exclusive (start of next day).
    """
    if date_from or date_to:
        df = parse_iso_date(date_from)
        dt = parse_iso_date(date_to)
        dt_end = (dt + timedelta(days=1)) if dt else None
        return (
            df.timestamp() if df else None,
            dt_end.timestamp() if dt_end else None,
            "",
            date_from or "",
            date_to or "",
        )

    preset = preset or "30d"
    days = next((d for k, _, d in PRESETS if k == preset), 30)
    if days is None:
        return None, None, "all", "", ""
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start = today - timedelta(days=days - 1)
    end = today + timedelta(days=1)
    return (
        start.timestamp(),
        end.timestamp(),
        preset,
        start.date().isoformat(),
        today.date().isoformat(),
    )


def day_range(date_str: str) -> tuple[float, float] | None:
    """Parse YYYY-MM-DD → (start_ts, end_ts) for that local-time day."""
    start = parse_iso_date(date_str)
    if not start:
        return None
    return start.timestamp(), (start + timedelta(days=1)).timestamp()
