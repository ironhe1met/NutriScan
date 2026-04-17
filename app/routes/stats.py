from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from ..db import get_stats
from ..layout import page

router = APIRouter()


@router.get("/stats")
async def stats():
    return await get_stats()


@router.get("/stats/dashboard", response_class=HTMLResponse)
async def stats_dashboard():
    data = await get_stats()

    rows_provider = ""
    for p in data["by_provider_model"]:
        rows_provider += (
            f"<tr><td>{p['provider']}</td><td>{p['model']}</td>"
            f"<td>{p['count']}</td><td>{p['successes']}</td>"
            f"<td>{int(p['avg_time_ms'] or 0)} ms</td></tr>"
        )
    if not rows_provider:
        rows_provider = '<tr><td colspan="5" style="text-align:center;color:#64748b;padding:24px">No data yet</td></tr>'

    rows_recent = ""
    for r in data["recent_requests"]:
        ts = datetime.fromtimestamp(r["timestamp"], tz=timezone.utc).strftime("%d.%m %H:%M")
        status = '<span style="color:#4ade80">OK</span>' if r["success"] else f'<span style="color:#f87171">ERR</span>'
        rows_recent += (
            f"<tr><td>{ts}</td><td>{r['provider']}</td><td>{r['model']}</td>"
            f"<td>{r['response_time_ms']} ms</td><td>{r.get('dish_name') or '-'}</td>"
            f"<td>{status}</td></tr>"
        )
    if not rows_recent:
        rows_recent = '<tr><td colspan="6" style="text-align:center;color:#64748b;padding:24px">No requests yet</td></tr>'

    body = f"""
<h1>Dashboard</h1>
<p class="subtitle">Overall statistics and recent activity</p>

<style>
  .cards {{ display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 32px; }}
  .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 20px 24px; flex: 1; min-width: 150px; }}
  .card .num {{ font-size: 2em; font-weight: 700; color: #38bdf8; }}
  .card .label {{ color: #94a3b8; font-size: 0.85em; margin-top: 4px; }}
  table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 12px; overflow: hidden; margin-top: 8px; }}
  th, td {{ padding: 10px 14px; text-align: left; border-bottom: 1px solid #334155; font-size: 0.92em; }}
  th {{ color: #94a3b8; font-weight: 500; background: #0f172a; font-size: 0.82em; text-transform: uppercase; letter-spacing: 0.5px; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #273449; }}
</style>

<div class="cards">
    <div class="card"><div class="num">{data['total_requests']}</div><div class="label">Total</div></div>
    <div class="card"><div class="num" style="color:#4ade80">{data['successful']}</div><div class="label">Success</div></div>
    <div class="card"><div class="num" style="color:#f87171">{data['failed']}</div><div class="label">Failed</div></div>
    <div class="card"><div class="num">{data['success_rate']}%</div><div class="label">Success Rate</div></div>
    <div class="card"><div class="num">{data['avg_response_time_ms']}</div><div class="label">Avg Response (ms)</div></div>
</div>

<h2>By Provider / Model</h2>
<table>
<tr><th>Provider</th><th>Model</th><th>Requests</th><th>Success</th><th>Avg Time</th></tr>
{rows_provider}
</table>

<h2>Recent Requests</h2>
<table>
<tr><th>Time</th><th>Provider</th><th>Model</th><th>Time</th><th>Dish</th><th>Status</th></tr>
{rows_recent}
</table>
"""
    return page("Dashboard", "stats", body)
