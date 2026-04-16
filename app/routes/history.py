from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from ..db import get_history, get_entry

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

    rows = ""
    for e in entries:
        ts = datetime.fromtimestamp(e["timestamp"], tz=timezone.utc).strftime("%d.%m %H:%M")
        r = e.get("result", {})
        total = r.get("total", {})
        macro = total.get("macronutrients", {})
        allergens = ", ".join(total.get("allergens", [])) or "-"

        # Ingredients summary
        ings = ", ".join(i["name"] for i in r.get("ingredients", [])[:5])
        if len(r.get("ingredients", [])) > 5:
            ings += f" +{len(r['ingredients']) - 5}"

        rows += f"""<tr>
            <td>{ts}</td>
            <td><strong>{e.get('dish_name', '?')}</strong></td>
            <td>{total.get('calories_kcal', 0)}</td>
            <td>{macro.get('protein_g', 0)}</td>
            <td>{macro.get('fat_g', 0)}</td>
            <td>{macro.get('carbs_g', 0)}</td>
            <td class="allergens">{allergens}</td>
            <td>{e.get('provider', '')}/{e.get('model', '')}</td>
            <td>{e.get('response_time_ms', 0)}ms</td>
            <td><a href="/history/{e['id']}">JSON</a></td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8"><title>NutriScan History</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #0f172a; color: #e2e8f0; max-width: 1100px; margin: 40px auto; padding: 0 20px; }}
  h1 {{ color: #38bdf8; }}
  .summary {{ color: #94a3b8; margin-bottom: 20px; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #1e293b; font-size: 0.9em; }}
  th {{ color: #64748b; font-weight: 500; position: sticky; top: 0; background: #0f172a; }}
  tr:hover {{ background: #1e293b; }}
  .allergens {{ color: #f87171; }}
  a {{ color: #38bdf8; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  strong {{ color: #f8fafc; }}
  .nav {{ margin-bottom: 20px; }}
  .nav a {{ margin-right: 16px; }}
</style>
</head><body>
<h1>NutriScan History</h1>
<div class="nav">
    <a href="/">Test page</a>
    <a href="/stats/dashboard">Dashboard</a>
    <a href="/history">JSON API</a>
</div>
<p class="summary">{len(entries)} analyses</p>
<table>
<tr>
    <th>Time</th><th>Dish</th><th>kcal</th><th>P</th><th>F</th><th>C</th>
    <th>Allergens</th><th>Provider</th><th>Time</th><th></th>
</tr>
{rows}
</table>
</body></html>"""
