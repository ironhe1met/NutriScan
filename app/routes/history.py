import html
import json as _json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse

from ..db import get_history, get_entry, count_history
from ..layout import page

router = APIRouter()

IMAGES_DIR = Path("data/images")


def _fmt_time(ts: float) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%d.%m.%Y %H:%M")


def _esc(v) -> str:
    return html.escape(str(v)) if v is not None else "-"


def _day_range(date_str: str) -> tuple[float, float] | None:
    """Parse YYYY-MM-DD → (start_ts, end_ts) for that local-time day."""
    try:
        start = datetime.fromisoformat(date_str).replace(hour=0, minute=0, second=0)
    except ValueError:
        return None
    return start.timestamp(), (start + timedelta(days=1)).timestamp()


@router.get("/history")
async def history_api(
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0),
    date: str | None = Query(None),
):
    df = dt_end = None
    if date:
        rng = _day_range(date)
        if rng:
            df, dt_end = rng
    entries = await get_history(limit=limit, offset=offset, date_from=df, date_to=dt_end)
    total = await count_history(date_from=df, date_to=dt_end)
    return {"total": total, "limit": limit, "offset": offset, "entries": entries}


@router.get("/history/image/{entry_id:int}")
async def history_image(entry_id: int):
    entry = await get_entry(entry_id)
    if not entry or not entry.get("image_filename"):
        raise HTTPException(status_code=404, detail="Image not found")
    image_path = IMAGES_DIR / entry["image_filename"]
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image file missing")
    return FileResponse(str(image_path))


@router.get("/history/view/all", response_class=HTMLResponse)
async def history_list_page(
    page_num: int = Query(1, alias="page", ge=1),
    date: str | None = Query(None),
):
    per_page = 100
    offset = (page_num - 1) * per_page

    df = dt_end = None
    date_filter_active = False
    if date:
        rng = _day_range(date)
        if rng:
            df, dt_end = rng
            date_filter_active = True

    total = await count_history(date_from=df, date_to=dt_end)
    entries = await get_history(limit=per_page, offset=offset, date_from=df, date_to=dt_end)
    total_pages = max(1, (total + per_page - 1) // per_page)

    page_qs = f"&date={date}" if date_filter_active else ""
    filter_banner = ""
    if date_filter_active:
        filter_banner = (
            f'<div class="filter-banner">Showing analyses for <strong>{_esc(date)}</strong> '
            f'<a href="/history/view/all">Clear filter ✕</a></div>'
        )

    if total == 0:
        empty_msg = (
            f"No analyses for {_esc(date)}. "
            f'<a href="/history/view/all" style="color:#38bdf8">Show all →</a>'
            if date_filter_active else
            'No analyses yet. <a href="/test" style="color:#38bdf8">Upload a photo →</a>'
        )
        body = f"""
<h1>History</h1>
<p class="subtitle">All saved analyses</p>
{filter_banner}
<style>
  .filter-banner {{ background: #1e293b; border: 1px solid #38bdf8; border-radius: 10px; padding: 12px 16px; margin-bottom: 16px; color: #94a3b8; font-size: 0.9em; display: flex; align-items: center; gap: 12px; }}
  .filter-banner strong {{ color: #38bdf8; }}
  .filter-banner a {{ color: #f87171; text-decoration: none; margin-left: auto; padding: 4px 10px; border-radius: 6px; border: 1px solid #334155; font-size: 0.85em; }}
  .filter-banner a:hover {{ border-color: #f87171; }}
</style>
<div style="background:#1e293b;border-radius:12px;padding:60px;text-align:center;color:#64748b">
    {empty_msg}
</div>
"""
        return page("History", "history", body)

    rows = ""
    for e in entries:
        ts = _fmt_time(e["timestamp"])
        r = e.get("result") or {}
        total_data = r.get("total") or {}
        macro = total_data.get("macronutrients") or {}
        allergens = ", ".join(total_data.get("allergens", [])) or "-"

        img_cell = (
            f'<img src="/history/image/{e["id"]}" alt="">'
            if e.get("image_filename") else '<div class="no-img"></div>'
        )

        rows += f"""<tr onclick="location.href='/history/view/{e['id']}'">
            <td class="thumb">{img_cell}</td>
            <td>{_esc(ts)}</td>
            <td><strong>{_esc(e.get('dish_name'))}</strong></td>
            <td>{_esc(total_data.get('calories_kcal', 0))}</td>
            <td>{_esc(macro.get('protein_g', 0))}</td>
            <td>{_esc(macro.get('fat_g', 0))}</td>
            <td>{_esc(macro.get('carbs_g', 0))}</td>
            <td class="allergens">{_esc(allergens)}</td>
            <td><span class="badge">{_esc(e.get('provider'))}</span> {_esc(e.get('model'))}</td>
            <td>{_esc(e.get('response_time_ms'))}ms</td>
        </tr>"""

    pag = ""
    if total_pages > 1:
        prev_cls = "disabled" if page_num <= 1 else ""
        next_cls = "disabled" if page_num >= total_pages else ""
        prev_link = f"/history/view/all?page={page_num - 1}{page_qs}" if page_num > 1 else "#"
        next_link = f"/history/view/all?page={page_num + 1}{page_qs}" if page_num < total_pages else "#"
        pag = f"""
<div class="pagination">
    <a href="{prev_link}" class="{prev_cls}">← Prev</a>
    <span class="page-info">Page {page_num} of {total_pages}</span>
    <a href="{next_link}" class="{next_cls}">Next →</a>
</div>
"""

    subtitle = (
        f"{total} analyses for {_esc(date)} — page {page_num} of {total_pages}"
        if date_filter_active else
        f"{total} analyses saved — page {page_num} of {total_pages}"
    )

    body = f"""
<h1>History</h1>
<p class="subtitle">{subtitle}</p>
{filter_banner}

<style>
  .filter-banner {{ background: #1e293b; border: 1px solid #38bdf8; border-radius: 10px; padding: 12px 16px; margin-bottom: 16px; color: #94a3b8; font-size: 0.9em; display: flex; align-items: center; gap: 12px; }}
  .filter-banner strong {{ color: #38bdf8; }}
  .filter-banner a {{ color: #f87171; text-decoration: none; margin-left: auto; padding: 4px 10px; border-radius: 6px; border: 1px solid #334155; font-size: 0.85em; }}
  .filter-banner a:hover {{ border-color: #f87171; }}
  table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 12px; overflow: hidden; }}
  th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #334155; font-size: 0.9em; }}
  th {{ color: #94a3b8; font-weight: 500; background: #0f172a; font-size: 0.78em; text-transform: uppercase; letter-spacing: 0.5px; }}
  tr:last-child td {{ border-bottom: none; }}
  tr {{ cursor: pointer; transition: background 0.1s; }}
  tr:hover td {{ background: #273449; }}
  .thumb {{ width: 56px; padding: 6px 8px; }}
  .thumb img {{ width: 48px; height: 48px; object-fit: cover; border-radius: 6px; display: block; }}
  .thumb .no-img {{ width: 48px; height: 48px; background: #0f172a; border-radius: 6px; }}
  .allergens {{ color: #f87171; font-size: 0.85em; }}
  strong {{ color: #f8fafc; }}
  .badge {{ background: #0f172a; padding: 2px 8px; border-radius: 6px; font-size: 0.8em; color: #38bdf8; }}
  .pagination {{ display: flex; align-items: center; justify-content: center; gap: 20px; margin-top: 24px; color: #94a3b8; font-size: 0.9em; }}
  .pagination a {{ color: #38bdf8; text-decoration: none; padding: 8px 16px; border: 1px solid #334155; border-radius: 8px; transition: all 0.15s; }}
  .pagination a:hover {{ background: #1e293b; border-color: #38bdf8; }}
  .pagination a.disabled {{ color: #475569; pointer-events: none; border-color: #1e293b; }}
  .page-info {{ color: #64748b; }}
</style>

<table>
<tr>
    <th></th><th>Time</th><th>Dish</th><th>kcal</th><th>P</th><th>F</th><th>C</th>
    <th>Allergens</th><th>AI</th><th>Time</th>
</tr>
{rows}
</table>
{pag}
"""
    return page("History", "history", body)


@router.get("/history/view/{entry_id:int}", response_class=HTMLResponse)
async def history_detail_page(entry_id: int):
    entry = await get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    r = entry.get("result") or {}
    total_data = r.get("total") or {}
    macro = total_data.get("macronutrients") or {}
    micro = total_data.get("micronutrients") or {}
    vitamins = micro.get("vitamins") or {}
    minerals = micro.get("minerals") or {}
    allergens = total_data.get("allergens", [])

    if entry.get("image_filename") and (IMAGES_DIR / entry["image_filename"]).exists():
        image_html = f'<img src="/history/image/{entry_id}" alt="">'
    else:
        image_html = '<div class="no-image">No image saved</div>'

    ts = _fmt_time(entry["timestamp"])
    provider = _esc(entry.get("provider"))
    model = _esc(entry.get("model"))
    elapsed = _esc(entry.get("response_time_ms"))
    img_size = entry.get("image_size_bytes")
    img_size_str = f"{img_size / 1024:.1f} KB" if img_size else "-"

    totals_html = f"""
<div class="totals">
    <div class="total-card highlight"><div class="num">{_esc(total_data.get('calories_kcal', 0))}</div><div class="lbl">Calories (kcal)</div></div>
    <div class="total-card"><div class="num">{_esc(macro.get('protein_g', 0))}</div><div class="lbl">Protein (g)</div></div>
    <div class="total-card"><div class="num">{_esc(macro.get('fat_g', 0))}</div><div class="lbl">Fat (g)</div></div>
    <div class="total-card"><div class="num">{_esc(macro.get('carbs_g', 0))}</div><div class="lbl">Carbs (g)</div></div>
    <div class="total-card"><div class="num">{_esc(macro.get('water_g', 0))}</div><div class="lbl">Water (g)</div></div>
</div>
"""

    extra_macro = []
    for key, label in [
        ("saturated_fat_g", "Saturated fat"), ("trans_fat_g", "Trans fat"),
        ("monounsaturated_fat_g", "Monounsat fat"), ("polyunsaturated_fat_g", "Polyunsat fat"),
        ("fiber_g", "Fiber"), ("sugars_g", "Sugars"), ("starch_g", "Starch"),
        ("cholesterol_mg", "Cholesterol (mg)"),
    ]:
        if key in macro:
            extra_macro.append(f"<div><span>{_esc(label)}:</span> <strong>{_esc(macro[key])}</strong></div>")
    extra_macro_html = f'<div class="extra-macro"><h3>Detailed macros</h3>{"".join(extra_macro)}</div>' if extra_macro else ""

    vit_html = ""
    if vitamins:
        items = "".join(f"<div><span>{_esc(k)}:</span> <strong>{_esc(v)}</strong></div>" for k, v in vitamins.items())
        vit_html = f'<div class="micro-block"><h3>Vitamins</h3>{items}</div>'

    min_html = ""
    if minerals:
        items = "".join(f"<div><span>{_esc(k)}:</span> <strong>{_esc(v)}</strong></div>" for k, v in minerals.items())
        min_html = f'<div class="micro-block"><h3>Minerals</h3>{items}</div>'

    ing_rows = ""
    for ing in r.get("ingredients", []):
        ing_macro = ing.get("macronutrients") or {}
        ing_allergens = ", ".join(ing.get("allergens", [])) or "-"
        ing_rows += f"""<tr>
            <td><strong>{_esc(ing.get('name'))}</strong></td>
            <td>{_esc(ing.get('weight_g', 0))}</td>
            <td>{_esc(ing.get('calories_kcal', 0))}</td>
            <td>{_esc(ing_macro.get('protein_g', 0))}</td>
            <td>{_esc(ing_macro.get('fat_g', 0))}</td>
            <td>{_esc(ing_macro.get('carbs_g', 0))}</td>
            <td class="allergens">{_esc(ing_allergens)}</td>
        </tr>"""

    allergens_html = ""
    if allergens:
        tags = "".join(f'<span class="allergen-tag">{_esc(a)}</span>' for a in allergens)
        allergens_html = f'<div class="allergens-banner"><span class="lbl">Allergens:</span> {tags}</div>'

    raw_json = html.escape(_json.dumps(r, indent=2, ensure_ascii=False))

    body = f"""
<div class="breadcrumb"><a href="/history/view/all">← Back to history</a></div>

<style>
  .breadcrumb {{ margin-bottom: 16px; }}
  .breadcrumb a {{ color: #38bdf8; text-decoration: none; font-size: 0.9em; }}
  .breadcrumb a:hover {{ text-decoration: underline; }}

  .detail-header {{ display: flex; gap: 24px; margin-bottom: 24px; align-items: flex-start; flex-wrap: wrap; }}
  .detail-header img {{ width: 280px; height: 280px; object-fit: cover; border-radius: 12px; flex-shrink: 0; }}
  .detail-header .no-image {{ width: 280px; height: 280px; background: #1e293b; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #64748b; flex-shrink: 0; }}
  .detail-info {{ flex: 1; min-width: 300px; }}
  .detail-info h1 {{ margin-bottom: 8px; }}
  .detail-meta {{ color: #64748b; font-size: 0.85em; margin-bottom: 16px; display: flex; gap: 8px; flex-wrap: wrap; }}
  .detail-meta span {{ background: #1e293b; padding: 4px 10px; border-radius: 6px; }}
  .detail-meta .badge-ai {{ color: #38bdf8; }}

  .allergens-banner {{ background: #450a0a; color: #fca5a5; padding: 10px 14px; border-radius: 8px; margin-bottom: 16px; font-size: 0.9em; }}
  .allergens-banner .lbl {{ color: #f87171; font-weight: 600; margin-right: 8px; }}
  .allergen-tag {{ display: inline-block; background: #7f1d1d; padding: 2px 8px; border-radius: 4px; margin-right: 4px; font-size: 0.85em; }}

  .totals {{ display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 24px; }}
  .total-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 14px 20px; flex: 1; min-width: 100px; }}
  .total-card.highlight {{ border-color: #38bdf8; }}
  .total-card .num {{ font-size: 1.6em; font-weight: 700; color: #f8fafc; }}
  .total-card.highlight .num {{ color: #38bdf8; }}
  .total-card .lbl {{ color: #94a3b8; font-size: 0.8em; margin-top: 2px; }}

  .micro-block, .extra-macro {{ background: #1e293b; border-radius: 10px; padding: 14px 20px; margin-bottom: 16px; }}
  .micro-block h3, .extra-macro h3 {{ color: #94a3b8; font-size: 0.85em; margin-bottom: 8px; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }}
  .micro-block > div:not(h3), .extra-macro > div:not(h3) {{ display: inline-block; background: #0f172a; padding: 4px 10px; border-radius: 6px; margin: 3px 3px 3px 0; font-size: 0.85em; }}
  .micro-block span, .extra-macro span {{ color: #64748b; margin-right: 6px; }}

  table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 10px; overflow: hidden; }}
  th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #334155; font-size: 0.9em; }}
  th {{ color: #94a3b8; font-weight: 500; background: #0f172a; font-size: 0.78em; text-transform: uppercase; letter-spacing: 0.5px; }}
  tr:last-child td {{ border-bottom: none; }}
  .allergens {{ color: #f87171; font-size: 0.85em; }}

  .json-toggle {{ background: none; border: 1px solid #334155; color: #64748b; border-radius: 6px; padding: 8px 14px; cursor: pointer; font-size: 0.85em; margin-top: 24px; }}
  .json-toggle:hover {{ border-color: #38bdf8; color: #38bdf8; }}
  .json-raw {{ background: #020617; border-radius: 8px; padding: 16px; margin-top: 12px; overflow-x: auto; font-family: 'SF Mono', Consolas, monospace; font-size: 0.78em; color: #94a3b8; white-space: pre-wrap; display: none; max-height: 600px; overflow-y: auto; }}
</style>

<div class="detail-header">
    {image_html}
    <div class="detail-info">
        <h1>{_esc(entry.get('dish_name'))}</h1>
        <div class="detail-meta">
            <span>{_esc(ts)}</span>
            <span class="badge-ai">{provider}/{model}</span>
            <span>{elapsed} ms</span>
            <span>{_esc(img_size_str)}</span>
            <span>#{entry_id}</span>
        </div>
        {allergens_html}
        {totals_html}
    </div>
</div>

{extra_macro_html}
{vit_html}
{min_html}

<h2>Ingredients ({len(r.get('ingredients', []))})</h2>
<table>
<tr><th>Name</th><th>Weight (g)</th><th>kcal</th><th>P (g)</th><th>F (g)</th><th>C (g)</th><th>Allergens</th></tr>
{ing_rows}
</table>

<button class="json-toggle" onclick="toggleJson()">Show raw JSON</button>
<pre class="json-raw" id="rawJson">{raw_json}</pre>

<script>
function toggleJson() {{
    const el = document.getElementById('rawJson');
    el.style.display = el.style.display === 'none' || !el.style.display ? 'block' : 'none';
}}
</script>
"""
    return page(entry.get("dish_name") or f"Analysis #{entry_id}", "history", body)


@router.get("/history/{entry_id:int}")
async def history_entry_api(entry_id: int):
    entry = await get_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    return entry
