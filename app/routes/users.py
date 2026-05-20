import html
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from ..db import (
    list_users,
    get_user_stats,
    get_user_history,
    count_user_history,
)
from ..layout import page
from ..utils.date_range import PRESETS, resolve_range

router = APIRouter()


def _esc(v) -> str:
    return html.escape(str(v)) if v is not None else "—"


def _fmt_ts(ts: float | None) -> str:
    if not ts:
        return "—"
    return datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M")


def _fmt_day(ts: float | None) -> str:
    if not ts:
        return "—"
    return datetime.fromtimestamp(ts).strftime("%d.%m.%Y")


def _initial_block(uid: str, type_: str) -> str:
    """Avatar-substitute: colored circle with first 2 chars of UID (or type icon)."""
    if type_ == "anon":
        ch = "?"
        bg = "#475569"
    elif type_ == "tg":
        ch = "T"
        bg = "#0ea5e9"
    else:  # mobile
        ch = uid[:2].upper() if uid and uid != "—" else "M"
        bg = "#8b5cf6"
    return (
        f'<span class="avatar" style="background:{bg}">{_esc(ch)}</span>'
    )


def _user_link(type_: str, uid: str | None) -> str:
    if type_ == "anon":
        return "/users/anon"
    return f"/users/{type_}/{uid}"


def _user_short(uid: str | None, type_: str) -> str:
    if type_ == "anon" or not uid or uid == "—":
        return "—"
    if type_ == "mobile" and len(uid) > 10:
        return f"{uid[:6]}…{uid[-4:]}"
    return uid


SHARED_USERS_STYLES = """
<style>
  .filter-bar { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; margin-bottom: 24px; padding: 12px 16px; background: #1e293b; border: 1px solid #334155; border-radius: 12px; }
  .chips { display: flex; gap: 6px; flex-wrap: wrap; }
  .chip { background: #0f172a; color: #94a3b8; padding: 6px 12px; border-radius: 8px; text-decoration: none; font-size: 0.88em; border: 1px solid transparent; transition: all 0.15s; }
  .chip:hover { color: #e2e8f0; border-color: #334155; }
  .chip.active { color: #38bdf8; border-color: #38bdf8; background: #0f172a; }

  table { width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 12px; overflow: hidden; }
  th, td { padding: 10px 14px; text-align: left; border-bottom: 1px solid #334155; font-size: 0.92em; vertical-align: middle; }
  th { color: #94a3b8; font-weight: 500; background: #0f172a; font-size: 0.78em; text-transform: uppercase; letter-spacing: 0.5px; }
  tr:last-child td { border-bottom: none; }
  tr.clickable { cursor: pointer; transition: background 0.1s; }
  tr.clickable:hover td { background: #273449; }

  .avatar { display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 50%; color: #fff; font-weight: 700; font-size: 0.85em; margin-right: 10px; vertical-align: middle; flex-shrink: 0; }
  .uid-cell { display: flex; align-items: center; gap: 0; }
  .uid-text { font-family: 'SF Mono', Consolas, monospace; font-size: 0.85em; color: #f8fafc; }
  .type-badge { display: inline-block; background: #0f172a; padding: 2px 8px; border-radius: 6px; font-size: 0.72em; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.5px; margin-left: 8px; }
  .type-badge.mobile { color: #c4b5fd; }
  .type-badge.tg { color: #7dd3fc; }
  .type-badge.anon { color: #94a3b8; }

  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin-bottom: 32px; }
  .card { background: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 16px 20px; }
  .card .num { font-size: 1.8em; font-weight: 700; color: #38bdf8; line-height: 1.1; }
  .card .label { color: #94a3b8; font-size: 0.78em; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }

  .breadcrumb { margin-bottom: 16px; }
  .breadcrumb a { color: #38bdf8; text-decoration: none; font-size: 0.9em; }
  .breadcrumb a:hover { text-decoration: underline; }

  .bar { position: relative; height: 22px; background: #0f172a; border-radius: 6px; overflow: hidden; min-width: 80px; }
  .bar-fill { height: 100%; background: linear-gradient(90deg, #38bdf8, #0ea5e9); border-radius: 6px; }
  .bar-num { position: absolute; top: 50%; left: 8px; transform: translateY(-50%); font-size: 0.82em; color: #f8fafc; font-weight: 600; text-shadow: 0 1px 2px rgba(0,0,0,0.5); }

  .empty { text-align: center; color: #64748b; padding: 24px; }
  .muted { color: #64748b; font-size: 0.85em; }
  .badge { background: #0f172a; padding: 2px 8px; border-radius: 6px; font-size: 0.8em; color: #38bdf8; }
  .pagination { display: flex; align-items: center; justify-content: center; gap: 20px; margin-top: 24px; color: #94a3b8; font-size: 0.9em; }
  .pagination a { color: #38bdf8; text-decoration: none; padding: 8px 16px; border: 1px solid #334155; border-radius: 8px; }
  .pagination a:hover { background: #1e293b; border-color: #38bdf8; }
  .pagination a.disabled { color: #475569; pointer-events: none; border-color: #1e293b; }
</style>
"""


def _filter_bar(active_preset: str) -> str:
    chips = []
    for key, label, _ in PRESETS:
        cls = "chip active" if key == active_preset else "chip"
        chips.append(f'<a class="{cls}" href="?range={key}">{label}</a>')
    return f'<div class="filter-bar"><div class="chips">{"".join(chips)}</div></div>'


@router.get("/users", response_class=HTMLResponse)
async def users_list_page(
    range_: str | None = Query(None, alias="range"),
):
    df, dt_end, active_preset, _, _ = resolve_range(range_, None, None)
    users = await list_users(date_from=df, date_to=dt_end, limit=500)

    rows = ""
    for u in users:
        uid = u["uid"]
        type_ = u["type"]
        avatar = _initial_block(uid or "?", type_)
        short_uid = _user_short(uid, type_)
        if type_ == "anon":
            short_uid_html = '<span class="uid-text" style="color:#64748b">(anonymous)</span>'
        else:
            short_uid_html = f'<span class="uid-text" title="{_esc(uid)}">{_esc(short_uid)}</span>'

        success_rate = round((u["successes"] or 0) / u["total"] * 100, 1) if u["total"] else 0
        cost_str = f'${u["cost"]:.4f}' if u["cost"] else '—'
        href = _user_link(type_, uid)
        rows += f"""<tr class="clickable" onclick="location.href='{href}'">
            <td><div class="uid-cell">{avatar}{short_uid_html}<span class="type-badge {type_}">{type_}</span></div></td>
            <td>{u["total"]}</td>
            <td>{u["successes"] or 0} <span class="muted">({success_rate}%)</span></td>
            <td>{cost_str}</td>
            <td>{_fmt_day(u["first_ts"])}</td>
            <td>{_fmt_day(u["last_ts"])}</td>
        </tr>"""

    if not rows:
        rows = '<tr><td colspan="6" class="empty">No users in this range</td></tr>'

    body = f"""
<h1>Users</h1>
<p class="subtitle">{len(users)} known users (mobile + Telegram + anonymous)</p>

{SHARED_USERS_STYLES}
{_filter_bar(active_preset)}

<table>
<tr>
  <th>User</th>
  <th>Total scans</th>
  <th>Success</th>
  <th>Cost</th>
  <th>First scan</th>
  <th>Last scan</th>
</tr>
{rows}
</table>

<p class="muted" style="margin-top:16px;font-size:0.85em">
  Mobile users: anonymous Firebase UID (28 chars, masked). Profile data (email, name, avatar)
  буде відображатись після інтеграції з Firebase у наступному релізі v1.2.0b.
</p>
"""
    return page("Users", "users", body)


@router.get("/users/anon", response_class=HTMLResponse)
async def users_anon_detail(
    range_: str | None = Query(None, alias="range"),
):
    return await _render_user_detail("anon", None, range_)


@router.get("/users/{user_type}/{user_id}", response_class=HTMLResponse)
async def users_detail_page(
    user_type: str,
    user_id: str,
    range_: str | None = Query(None, alias="range"),
):
    if user_type not in ("mobile", "tg"):
        raise HTTPException(status_code=404, detail="Unknown user type")
    return await _render_user_detail(user_type, user_id, range_)


async def _render_user_detail(user_type: str, user_id: str | None, range_: str | None) -> HTMLResponse:
    df, dt_end, active_preset, _, _ = resolve_range(range_, None, None)
    stats = await get_user_stats(user_type, user_id, date_from=df, date_to=dt_end)

    # Recent 50 scans for this user (no separate pagination yet)
    history = await get_user_history(user_type, user_id, limit=50, offset=0,
                                     date_from=df, date_to=dt_end)
    total_history = await count_user_history(user_type, user_id,
                                             date_from=df, date_to=dt_end)

    if user_type == "anon":
        header_id_html = '<span class="uid-text" style="color:#64748b">(anonymous bucket — no user_id)</span>'
        avatar = _initial_block("?", "anon")
        title = "Anonymous"
    elif user_type == "tg":
        header_id_html = f'<span class="uid-text">{_esc(user_id)}</span>'
        avatar = _initial_block(user_id or "?", "tg")
        title = f"Telegram user {user_id}"
    else:
        header_id_html = f'<span class="uid-text" title="{_esc(user_id)}">{_esc(user_id)}</span>'
        avatar = _initial_block(user_id or "?", "mobile")
        title = f"Mobile user {_user_short(user_id, 'mobile')}"

    cards_html = f"""
<div class="cards">
    <div class="card"><div class="num">{stats['total']}</div><div class="label">Total scans</div></div>
    <div class="card"><div class="num" style="color:#4ade80">{stats['successes']}</div><div class="label">Success</div></div>
    <div class="card"><div class="num" style="color:#f87171">{stats['failed']}</div><div class="label">Failed</div></div>
    <div class="card"><div class="num">{stats['success_rate']}%</div><div class="label">Success Rate</div></div>
    <div class="card"><div class="num">${stats['total_cost']:.4f}</div><div class="label">Total cost</div></div>
    <div class="card"><div class="num">{stats['avg_per_day']}</div><div class="label">Avg / day</div></div>
    <div class="card"><div class="num">{stats['days_active']}</div><div class="label">Days active</div></div>
    <div class="card"><div class="num">{stats['avg_response_ms']}</div><div class="label">Avg time (ms)</div></div>
</div>
"""

    # by_day
    by_day = stats["by_day"]
    by_day_rows = ""
    if by_day:
        max_count = max(d["count"] for d in by_day) or 1
        for d in by_day:
            width = round(d["count"] / max_count * 100, 1)
            cost = f'${d["cost"]:.4f}' if d["cost"] else '—'
            by_day_rows += (
                f'<tr><td><strong>{d["day"]}</strong></td>'
                f'<td><div class="bar"><div class="bar-fill" style="width:{width}%"></div>'
                f'<span class="bar-num">{d["count"]}</span></div></td>'
                f'<td>{d["successes"]}</td>'
                f'<td>{cost}</td></tr>'
            )
    else:
        by_day_rows = '<tr><td colspan="4" class="empty">No data</td></tr>'

    # by_provider
    by_prov_rows = ""
    for p in stats["by_provider"]:
        cost = f'${p["cost"]:.4f}' if p["cost"] else '—'
        by_prov_rows += (
            f'<tr><td>{p["provider"]}</td><td>{p["model"]}</td>'
            f'<td>{p["count"]}</td><td>{cost}</td></tr>'
        )
    if not by_prov_rows:
        by_prov_rows = '<tr><td colspan="4" class="empty">No data</td></tr>'

    # history rows
    hist_rows = ""
    for e in history:
        ts = _fmt_ts(e["timestamp"])
        if e["success"]:
            status = '<span style="color:#4ade80">OK</span>'
        else:
            status = '<span style="color:#f87171">ERR</span>'
        dish = _esc(e.get("dish_name"))
        cost = f'${e["cost_usd"]:.4f}' if e.get("cost_usd") else '—'
        link = f"/history/view/{e['id']}" if e["success"] else "#"
        cursor_style = 'class="clickable"' if e["success"] else ''
        onclick = f'''onclick="location.href='{link}'"''' if e["success"] else ''
        hist_rows += (
            f'<tr {cursor_style} {onclick}>'
            f'<td>{ts}</td>'
            f'<td><span class="badge">{_esc(e["provider"])}</span> {_esc(e["model"])}</td>'
            f'<td><strong>{dish}</strong></td>'
            f'<td>{cost}</td>'
            f'<td>{e["response_time_ms"]} ms</td>'
            f'<td>{status}</td>'
            f'</tr>'
        )
    if not hist_rows:
        hist_rows = '<tr><td colspan="6" class="empty">No scans</td></tr>'

    body = f"""
<div class="breadcrumb"><a href="/users">← All users</a></div>

<h1>{_esc(title)}</h1>
<p class="subtitle">First: {_fmt_ts(stats['first_ts'])} · Last: {_fmt_ts(stats['last_ts'])} · Tokens: {stats['input_tokens']} in / {stats['output_tokens']} out</p>

{SHARED_USERS_STYLES}
<div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;padding:12px 16px;background:#1e293b;border-radius:10px;border:1px solid #334155">
  {avatar}{header_id_html}<span class="type-badge {user_type}">{user_type}</span>
</div>

{_filter_bar(active_preset)}
{cards_html}

<h2>By Day ({len(by_day)})</h2>
<table>
<tr><th>Day</th><th>Scans</th><th>Success</th><th>Cost</th></tr>
{by_day_rows}
</table>

<h2>By Provider / Model</h2>
<table>
<tr><th>Provider</th><th>Model</th><th>Scans</th><th>Cost</th></tr>
{by_prov_rows}
</table>

<h2>Recent scans ({len(history)} of {total_history})</h2>
<table>
<tr><th>Time</th><th>AI</th><th>Dish</th><th>Cost</th><th>Took</th><th>Status</th></tr>
{hist_rows}
</table>
"""
    return page(title, "users", body)
