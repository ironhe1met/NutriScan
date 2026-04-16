from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from ..db import get_stats

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
            f"<td>{int(p['avg_time_ms'])} ms</td></tr>"
        )

    rows_recent = ""
    for r in data["recent_requests"]:
        from datetime import datetime, timezone
        ts = datetime.fromtimestamp(r["timestamp"], tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
        status = "OK" if r["success"] else f"ERR: {r.get('error', '')[:40]}"
        rows_recent += (
            f"<tr><td>{ts}</td><td>{r['provider']}</td><td>{r['model']}</td>"
            f"<td>{r['response_time_ms']} ms</td><td>{r.get('dish_name', '-')}</td>"
            f"<td>{status}</td></tr>"
        )

    return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8"><title>NutriScan Stats</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; background: #0f172a; color: #e2e8f0; }}
  h1 {{ color: #38bdf8; }} h2 {{ color: #94a3b8; margin-top: 2em; }}
  .cards {{ display: flex; gap: 16px; flex-wrap: wrap; }}
  .card {{ background: #1e293b; border-radius: 12px; padding: 20px 28px; min-width: 150px; }}
  .card .num {{ font-size: 2em; font-weight: bold; color: #38bdf8; }}
  .card .label {{ color: #94a3b8; font-size: 0.9em; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
  th, td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #334155; }}
  th {{ color: #94a3b8; font-weight: 500; }}
</style>
</head><body>
<h1>NutriScan Dashboard</h1>
<div class="cards">
  <div class="card"><div class="num">{data['total_requests']}</div><div class="label">Total</div></div>
  <div class="card"><div class="num">{data['successful']}</div><div class="label">Success</div></div>
  <div class="card"><div class="num">{data['failed']}</div><div class="label">Failed</div></div>
  <div class="card"><div class="num">{data['success_rate']}%</div><div class="label">Rate</div></div>
  <div class="card"><div class="num">{data['avg_response_time_ms']}</div><div class="label">Avg ms</div></div>
</div>
<h2>By Provider / Model</h2>
<table><tr><th>Provider</th><th>Model</th><th>Requests</th><th>OK</th><th>Avg Time</th></tr>{rows_provider}</table>
<h2>Recent Requests</h2>
<table><tr><th>Time</th><th>Provider</th><th>Model</th><th>Time</th><th>Dish</th><th>Status</th></tr>{rows_recent}</table>
</body></html>"""
