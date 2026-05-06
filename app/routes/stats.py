from datetime import datetime
from urllib.parse import urlencode

from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from ..db import get_stats
from ..layout import page
from ..utils.date_range import PRESETS, resolve_range


def _drill_qs(active_preset: str, from_iso: str, to_iso: str, **extra) -> str:
    """Build query string preserving the dashboard's date filter for drill-down links."""
    params: dict = {}
    if from_iso and to_iso:
        params["from"] = from_iso
        params["to"] = to_iso
    elif active_preset and active_preset != "all":
        params["range"] = active_preset
    params.update(extra)
    return "?" + urlencode(params) if params else ""


router = APIRouter()


@router.get("/stats")
async def stats_api(
    range_: str | None = Query(None, alias="range"),
    date_from: str | None = Query(None, alias="from"),
    date_to: str | None = Query(None, alias="to"),
):
    df, dt_end, *_ = resolve_range(range_, date_from, date_to)
    return await get_stats(date_from=df, date_to=dt_end)


@router.get("/stats/dashboard", response_class=HTMLResponse)
async def stats_dashboard(
    range_: str | None = Query(None, alias="range"),
    date_from: str | None = Query(None, alias="from"),
    date_to: str | None = Query(None, alias="to"),
):
    df, dt_end, active_preset, from_iso, to_iso = resolve_range(range_, date_from, date_to)
    data = await get_stats(date_from=df, date_to=dt_end)

    chips = []
    for key, label, _ in PRESETS:
        cls = "chip active" if key == active_preset else "chip"
        chips.append(f'<a class="{cls}" href="/stats/dashboard?range={key}">{label}</a>')
    chips_html = "".join(chips)

    custom_active_cls = "active" if not active_preset else ""
    filter_bar = f"""
<div class="filter-bar">
  <div class="chips">{chips_html}</div>
  <form class="custom-range {custom_active_cls}" method="get" action="/stats/dashboard">
    <label>From <input type="date" name="from" value="{from_iso}"></label>
    <label>To <input type="date" name="to" value="{to_iso}"></label>
    <button type="submit">Apply</button>
  </form>
</div>
"""

    peak = data["peak_day"]
    peak_text = f"{peak['day']} ({peak['count']})" if peak else "—"

    success_drill = "/history/view/all" + _drill_qs(active_preset, from_iso, to_iso, status="success")
    failed_drill = "/history/view/all" + _drill_qs(active_preset, from_iso, to_iso, status="failed")

    cards_html = f"""
<div class="cards">
    <div class="card"><div class="num">{data['total_requests']}</div><div class="label">Total</div></div>
    <a class="card card-link" href="{success_drill}"><div class="num" style="color:#4ade80">{data['successful']}</div><div class="label">Success ↗</div></a>
    <a class="card card-link card-failed" href="{failed_drill}"><div class="num" style="color:#f87171">{data['failed']}</div><div class="label">Failed ↗</div></a>
    <div class="card"><div class="num">{data['success_rate']}%</div><div class="label">Success Rate</div></div>
    <div class="card"><div class="num">{data['avg_response_time_ms']}</div><div class="label">Avg Response (ms)</div></div>
    <div class="card"><div class="num">{data['avg_per_day']}</div><div class="label">Avg / day</div></div>
    <div class="card"><div class="num">{data['days_active']}</div><div class="label">Days active</div></div>
    <div class="card"><div class="num" style="font-size:1.1em">{peak_text}</div><div class="label">Peak day</div></div>
</div>
"""

    by_day = data["by_day"]
    rows_day = ""
    if by_day:
        max_count = max(d["count"] for d in by_day) or 1
        for d in by_day:
            day = d["day"]
            count = d["count"]
            successes = d["successes"]
            failed = count - successes
            avg_ms = int(d["avg_time_ms"] or 0)
            width = round(count / max_count * 100, 1)
            success_rate = round(successes / count * 100, 1) if count else 0
            failed_cell = (
                f'<a class="failed-pill" href="/history/view/all?status=failed&date={day}" '
                f'onclick="event.stopPropagation()">{failed}</a>'
                if failed > 0 else '<span class="muted">0</span>'
            )
            rows_day += (
                f'<tr class="day-row" onclick="location.href=\'/history/view/all?status=success&date={day}\'">'
                f'<td><strong>{day}</strong></td>'
                f'<td><div class="bar"><div class="bar-fill" style="width:{width}%"></div>'
                f'<span class="bar-num">{count}</span></div></td>'
                f'<td>{successes} <span class="muted">({success_rate}%)</span></td>'
                f'<td>{failed_cell}</td>'
                f'<td>{avg_ms} ms</td>'
                f'</tr>'
            )
    else:
        rows_day = '<tr><td colspan="5" class="empty">No requests in this range</td></tr>'

    rows_provider = ""
    for p in data["by_provider_model"]:
        rows_provider += (
            f"<tr><td>{p['provider']}</td><td>{p['model']}</td>"
            f"<td>{p['count']}</td><td>{p['successes']}</td>"
            f"<td>{int(p['avg_time_ms'] or 0)} ms</td></tr>"
        )
    if not rows_provider:
        rows_provider = '<tr><td colspan="5" class="empty">No data</td></tr>'

    rows_recent = ""
    for r in data["recent_requests"]:
        ts = datetime.fromtimestamp(r["timestamp"]).strftime("%d.%m %H:%M")
        if r["success"]:
            status_cell = '<span style="color:#4ade80">OK</span>'
        else:
            status_cell = f'<a class="err-link" href="{failed_drill}">ERR ↗</a>'
        rows_recent += (
            f"<tr><td>{ts}</td><td>{r['provider']}</td><td>{r['model']}</td>"
            f"<td>{r['response_time_ms']} ms</td><td>{r.get('dish_name') or '-'}</td>"
            f"<td>{status_cell}</td></tr>"
        )
    if not rows_recent:
        rows_recent = '<tr><td colspan="6" class="empty">No requests</td></tr>'

    body = f"""
<h1>Dashboard</h1>
<p class="subtitle">Statistics and activity</p>

<style>
  .filter-bar {{ display: flex; gap: 16px; align-items: center; flex-wrap: wrap; margin-bottom: 24px; padding: 12px 16px; background: #1e293b; border: 1px solid #334155; border-radius: 12px; }}
  .chips {{ display: flex; gap: 6px; flex-wrap: wrap; }}
  .chip {{ background: #0f172a; color: #94a3b8; padding: 6px 12px; border-radius: 8px; text-decoration: none; font-size: 0.88em; border: 1px solid transparent; transition: all 0.15s; }}
  .chip:hover {{ color: #e2e8f0; border-color: #334155; }}
  .chip.active {{ color: #38bdf8; border-color: #38bdf8; background: #0f172a; }}
  .custom-range {{ display: flex; gap: 8px; align-items: center; margin-left: auto; color: #64748b; font-size: 0.85em; }}
  .custom-range.active label {{ color: #38bdf8; }}
  .custom-range label {{ display: flex; gap: 6px; align-items: center; }}
  .custom-range input[type=date] {{ background: #0f172a; color: #e2e8f0; border: 1px solid #334155; border-radius: 6px; padding: 5px 8px; font-size: 0.9em; color-scheme: dark; }}
  .custom-range button {{ background: #38bdf8; color: #0f172a; border: none; border-radius: 6px; padding: 6px 14px; cursor: pointer; font-weight: 600; font-size: 0.85em; }}
  .custom-range button:hover {{ background: #7dd3fc; }}

  .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 32px; }}
  .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 16px 20px; display: block; text-decoration: none; }}
  .card .num {{ font-size: 1.8em; font-weight: 700; color: #38bdf8; line-height: 1.1; }}
  .card .label {{ color: #94a3b8; font-size: 0.78em; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }}
  .card-link {{ cursor: pointer; transition: all 0.15s; }}
  .card-link:hover {{ border-color: #475569; background: #273449; }}
  .card-link.card-failed:hover {{ border-color: #f87171; }}

  .failed-pill {{ display: inline-block; background: #450a0a; color: #fca5a5; padding: 2px 10px; border-radius: 999px; font-size: 0.85em; font-weight: 600; text-decoration: none; min-width: 26px; text-align: center; transition: all 0.15s; }}
  .failed-pill:hover {{ background: #7f1d1d; color: #fff; }}
  .err-link {{ color: #f87171; text-decoration: none; font-weight: 600; font-size: 0.85em; }}
  .err-link:hover {{ text-decoration: underline; }}

  table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 12px; overflow: hidden; margin-top: 8px; }}
  th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid #334155; font-size: 0.92em; }}
  th {{ color: #94a3b8; font-weight: 500; background: #0f172a; font-size: 0.78em; text-transform: uppercase; letter-spacing: 0.5px; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #273449; }}
  .empty {{ text-align: center; color: #64748b; padding: 24px; }}
  .muted {{ color: #64748b; font-size: 0.85em; }}

  .day-table tr {{ cursor: pointer; }}
  .bar {{ position: relative; height: 22px; background: #0f172a; border-radius: 6px; overflow: hidden; min-width: 80px; }}
  .bar-fill {{ height: 100%; background: linear-gradient(90deg, #38bdf8, #0ea5e9); border-radius: 6px; }}
  .bar-num {{ position: absolute; top: 50%; left: 8px; transform: translateY(-50%); font-size: 0.82em; color: #f8fafc; font-weight: 600; text-shadow: 0 1px 2px rgba(0,0,0,0.5); }}
</style>

{filter_bar}
{cards_html}

<h2>By Day ({len(by_day)})</h2>
<table class="day-table">
<tr><th>Day</th><th>Requests</th><th>Success</th><th>Failed</th><th>Avg time</th></tr>
{rows_day}
</table>

<h2>By Provider / Model</h2>
<table>
<tr><th>Provider</th><th>Model</th><th>Requests</th><th>Success</th><th>Avg Time</th></tr>
{rows_provider}
</table>

<h2>Recent Requests (last 20)</h2>
<table>
<tr><th>Time</th><th>Provider</th><th>Model</th><th>Time</th><th>Dish</th><th>Status</th></tr>
{rows_recent}
</table>
"""
    return page("Dashboard", "stats", body)
