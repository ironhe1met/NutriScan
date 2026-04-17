from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from ..db import get_history, get_entry
from ..layout import page

router = APIRouter()


@router.get("/history")
async def history(limit: int = Query(50, le=200), offset: int = Query(0, ge=0)):
    return await get_history(limit=limit, offset=offset)


@router.get("/history/{entry_id}")
async def history_entry(entry_id: int):
    entry = await get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry


@router.get("/history/view/all", response_class=HTMLResponse)
async def history_page():
    entries = await get_history(limit=100)

    if not entries:
        body = f"""
<h1>History</h1>
<p class="subtitle">All saved analyses</p>
<div style="background:#1e293b;border-radius:12px;padding:60px;text-align:center;color:#64748b">
    No analyses yet. <a href="/" style="color:#38bdf8">Upload a photo →</a>
</div>
"""
        return page("History", "history", body)

    rows = ""
    for e in entries:
        ts = datetime.fromtimestamp(e["timestamp"], tz=timezone.utc).strftime("%d.%m %H:%M")
        r = e.get("result", {})
        total = r.get("total", {})
        macro = total.get("macronutrients", {})
        allergens = ", ".join(total.get("allergens", [])) or "-"

        rows += f"""<tr>
            <td>{ts}</td>
            <td><strong>{e.get('dish_name') or '?'}</strong></td>
            <td>{total.get('calories_kcal', 0)}</td>
            <td>{macro.get('protein_g', 0)}</td>
            <td>{macro.get('fat_g', 0)}</td>
            <td>{macro.get('carbs_g', 0)}</td>
            <td class="allergens">{allergens}</td>
            <td><span class="badge">{e.get('provider', '')}</span> {e.get('model', '')}</td>
            <td>{e.get('response_time_ms', 0)}ms</td>
            <td><a href="/history/{e['id']}" target="_blank">JSON</a></td>
        </tr>"""

    body = f"""
<h1>History</h1>
<p class="subtitle">{len(entries)} analyses saved</p>

<style>
  table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 12px; overflow: hidden; }}
  th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #334155; font-size: 0.9em; }}
  th {{ color: #94a3b8; font-weight: 500; background: #0f172a; font-size: 0.78em; text-transform: uppercase; letter-spacing: 0.5px; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #273449; }}
  .allergens {{ color: #f87171; font-size: 0.85em; }}
  strong {{ color: #f8fafc; }}
  .badge {{ background: #0f172a; padding: 2px 8px; border-radius: 6px; font-size: 0.8em; color: #38bdf8; }}
  a {{ color: #38bdf8; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
</style>

<table>
<tr>
    <th>Time</th><th>Dish</th><th>kcal</th><th>P</th><th>F</th><th>C</th>
    <th>Allergens</th><th>AI</th><th>Time</th><th></th>
</tr>
{rows}
</table>
"""
    return page("History", "history", body)
