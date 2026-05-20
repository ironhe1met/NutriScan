import asyncio
import html
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse

from ..config import settings
from ..db import (
    list_users,
    get_user_stats,
    get_user_history,
    count_user_history,
    get_cached_mobile_user,
    get_cached_mobile_users,
    upsert_mobile_user,
    mobile_user_cache_stale,
)
from ..firebase import get_user_profile as fb_get_user_profile, is_enabled as fb_is_enabled, get_init_error as fb_init_error
from ..layout import page
from ..utils.date_range import PRESETS, resolve_range, day_range

logger = logging.getLogger("nutriscan.users")
router = APIRouter()


async def _refresh_mobile_profile(uid: str) -> dict | None:
    """Fetch from Firebase, persist to cache. Returns the profile (or None)."""
    profile = await fb_get_user_profile(uid)
    if profile is None:
        # firebase disabled or hard-error — still record a stub so we don't re-hit constantly
        await upsert_mobile_user(uid, None, error="firebase_unavailable")
        return None
    await upsert_mobile_user(uid, profile)
    return profile


async def _get_profile_with_refresh(uid: str) -> dict | None:
    """Return cached profile; trigger background refresh if stale/missing."""
    cached = await get_cached_mobile_user(uid)
    stale = await mobile_user_cache_stale(uid, settings.firebase_cache_ttl_sec)
    if stale and fb_is_enabled():
        # Fire and forget; current request returns the (possibly stale or None) cache
        asyncio.create_task(_refresh_mobile_profile(uid))
    return cached


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
  .avatar-img { width: 32px; height: 32px; border-radius: 50%; object-fit: cover; margin-right: 10px; flex-shrink: 0; background: #0f172a; }
  .ident-stack { display: inline-block; vertical-align: middle; }
  .ident-name { color: #f8fafc; font-weight: 600; font-size: 0.92em; line-height: 1.2; }
  .ident-sub { color: #64748b; font-size: 0.78em; line-height: 1.2; }
  .profile-card { display: flex; align-items: center; gap: 16px; padding: 16px 20px; background: #1e293b; border: 1px solid #334155; border-radius: 12px; margin-bottom: 20px; }
  .profile-card .avatar, .profile-card .avatar-img { width: 56px; height: 56px; font-size: 1.3em; margin-right: 0; }
  .profile-card .ident-name { font-size: 1.15em; }
  .profile-card .ident-sub { font-size: 0.88em; }
  .profile-extra { display: flex; gap: 12px; margin-left: auto; flex-wrap: wrap; }
  .profile-extra .field { background: #0f172a; padding: 4px 10px; border-radius: 6px; font-size: 0.8em; color: #94a3b8; }
  .profile-extra .field strong { color: #f8fafc; }
  .fs-card { background: #020617; border: 1px solid #334155; border-radius: 8px; padding: 12px; font-family: 'SF Mono', Consolas, monospace; font-size: 0.78em; color: #94a3b8; white-space: pre-wrap; word-break: break-word; max-height: 320px; overflow: auto; }

  /* Subscription / plan pill (neutral wording until Q-017 confirmed) */
  .plan-pill { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 999px; font-size: 0.78em; font-weight: 600; }
  .plan-pill.active { background: #064e3b; color: #6ee7b7; }
  .plan-pill.inactive { background: #1e293b; color: #94a3b8; border: 1px solid #334155; }
  .plan-pill::before { content: "●"; font-size: 0.7em; }

  /* Structured profile section */
  .profile-section { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 24px; }
  .profile-section .pf { background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 12px 14px; }
  .profile-section .pf-label { color: #64748b; font-size: 0.72em; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
  .profile-section .pf-value { color: #f8fafc; font-size: 0.95em; font-weight: 500; line-height: 1.3; }
  .profile-section .pf-value .secondary { color: #64748b; font-size: 0.82em; font-weight: 400; margin-left: 4px; }
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

    # Batch-fetch cached profiles for all mobile users
    mobile_uids = [u["uid"] for u in users if u["type"] == "mobile" and u.get("uid")]
    cache = await get_cached_mobile_users(mobile_uids) if mobile_uids else {}

    rows = ""
    for u in users:
        uid = u["uid"]
        type_ = u["type"]
        profile = cache.get(uid) if type_ == "mobile" else None
        avatar = _avatar_for(uid or "?", type_, profile)
        ident_cell = _ident_cell(uid, type_, profile)

        success_rate = round((u["successes"] or 0) / u["total"] * 100, 1) if u["total"] else 0
        cost_str = f'${u["cost"]:.4f}' if u["cost"] else '—'
        href = _user_link(type_, uid)
        rows += f"""<tr class="clickable" onclick="location.href='{href}'">
            <td><div class="uid-cell">{avatar}{ident_cell}<span class="type-badge {type_}">{type_}</span></div></td>
            <td>{u["total"]}</td>
            <td>{u["successes"] or 0} <span class="muted">({success_rate}%)</span></td>
            <td>{cost_str}</td>
            <td>{_fmt_day(u["first_ts"])}</td>
            <td>{_fmt_day(u["last_ts"])}</td>
        </tr>"""

    if not rows:
        rows = '<tr><td colspan="6" class="empty">No users in this range</td></tr>'

    fb_status = _firebase_status_banner()

    body = f"""
<h1>Users</h1>
<p class="subtitle">{len(users)} known users (mobile + Telegram + anonymous)</p>

{SHARED_USERS_STYLES}
{fb_status}
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
"""
    return page("Users", "users", body)


def _firebase_status_banner() -> str:
    if fb_is_enabled():
        return ""
    reason = fb_init_error() or "not configured"
    return (
        f'<div style="background:#1e293b;border:1px solid #f59e0b;border-radius:10px;'
        f'padding:10px 14px;margin-bottom:16px;color:#fcd34d;font-size:0.88em">'
        f'⚠ Firebase profile fetch is OFF — showing only UIDs. Reason: '
        f'<code>{_esc(reason)}</code></div>'
    )


def _avatar_for(uid: str, type_: str, profile: dict | None) -> str:
    """Real photo if Firebase profile has photo_url, else colored initial block."""
    if profile and profile.get("photo_url"):
        return f'<img class="avatar-img" src="{_esc(profile["photo_url"])}" alt="" referrerpolicy="no-referrer">'
    return _initial_block(uid, type_)


def _detail_title(user_type: str, user_id: str | None, profile: dict | None) -> str:
    if user_type == "anon":
        return "Anonymous"
    if user_type == "tg":
        return f"Telegram user {user_id}"
    if profile and profile.get("display_name"):
        return profile["display_name"]
    return f"Mobile user {_user_short(user_id, 'mobile')}"


def _profile_card_for(user_type: str, user_id: str | None, profile: dict | None) -> str:
    if user_type == "anon":
        return (
            f'<div class="profile-card">{_initial_block("?", "anon")}'
            f'<div class="ident-stack"><div class="ident-name">Anonymous</div>'
            f'<div class="ident-sub">requests without user_id / pre-v1.2 history</div></div></div>'
        )
    if user_type == "tg":
        return (
            f'<div class="profile-card">{_initial_block(user_id or "?", "tg")}'
            f'<div class="ident-stack"><div class="ident-name">Telegram user</div>'
            f'<div class="ident-sub">id: {_esc(user_id)}</div></div>'
            f'<span class="type-badge tg" style="margin-left:auto">tg</span></div>'
        )

    # mobile
    avatar = _avatar_for(user_id or "?", "mobile", profile)
    if profile and (profile.get("display_name") or profile.get("email")):
        name = profile.get("display_name") or "—"
        email = profile.get("email") or ""
        ident = (
            f'<div class="ident-stack"><div class="ident-name">{_esc(name)}</div>'
            f'<div class="ident-sub">{_esc(email)}</div></div>'
        )
    else:
        ident = (
            f'<div class="ident-stack"><div class="ident-name">Mobile user</div>'
            f'<div class="ident-sub" title="{_esc(user_id)}">uid: {_esc(user_id)}</div></div>'
        )

    extras = []
    fs = (profile or {}).get("firestore") or {}
    if profile:
        # Plan / subscription pill — based on is_plan_activated (Q-017 still open)
        if "is_plan_activated" in fs:
            if fs["is_plan_activated"]:
                extras.append('<span class="plan-pill active" title="is_plan_activated=True (Q-017)">Plan active</span>')
            else:
                extras.append('<span class="plan-pill inactive" title="is_plan_activated=False (Q-017)">Plan inactive</span>')

        cc = profile.get("custom_claims") or {}
        if cc.get("tier") or cc.get("subscription"):
            tier = cc.get("tier") or cc.get("subscription")
            extras.append(f'<span class="field">tier: <strong>{_esc(tier)}</strong></span>')
        if profile.get("phone_number"):
            extras.append(f'<span class="field">phone: <strong>{_esc(profile["phone_number"])}</strong></span>')
        if profile.get("email_verified") is False:
            extras.append('<span class="field" style="color:#fca5a5">email not verified</span>')
        if profile.get("disabled"):
            extras.append('<span class="field" style="color:#f87171">disabled</span>')
        if profile.get("fetched_at"):
            try:
                age_min = int((datetime.now().timestamp() - profile["fetched_at"]) / 60)
                extras.append(f'<span class="field">cached {age_min}m ago</span>')
            except Exception:
                pass
        if profile.get("fetch_error"):
            extras.append(
                f'<span class="field" style="color:#fcd34d" title="Firebase did not return data">'
                f'⚠ {_esc(profile["fetch_error"])}</span>'
            )
    else:
        extras.append('<span class="field" style="color:#fcd34d">no Firebase data yet</span>')

    refresh_btn = (
        f'<form method="post" action="/users/mobile/{_esc(user_id)}/refresh" style="margin:0">'
        f'<button type="submit" class="field" '
        f'style="background:#0f172a;border:1px solid #334155;color:#38bdf8;cursor:pointer;'
        f'padding:4px 10px;border-radius:6px;font-size:0.8em">↻ Refresh</button></form>'
    ) if fb_is_enabled() else ""

    structured_profile = _profile_section_html(profile)

    firestore_block = ""
    if profile and profile.get("firestore"):
        import json as _json
        try:
            fs_text = _json.dumps(profile["firestore"], indent=2, ensure_ascii=False, default=str)
        except Exception:
            fs_text = str(profile["firestore"])
        firestore_block = (
            f'<details style="margin-bottom:16px"><summary style="cursor:pointer;color:#94a3b8;'
            f'font-size:0.88em">Raw Firestore document (users/{_esc(user_id)})</summary>'
            f'<pre class="fs-card">{_esc(fs_text)}</pre></details>'
        )

    return (
        f'<div class="profile-card">{avatar}{ident}'
        f'<div class="profile-extra">{"".join(extras)}'
        f'<span class="type-badge mobile">mobile</span>{refresh_btn}</div></div>'
        f'{structured_profile}'
        f'{firestore_block}'
    )


def _profile_section_html(profile: dict | None) -> str:
    """Render demographic / fitness profile in a structured grid (from Firestore data)."""
    if not profile:
        return ""
    fs = profile.get("firestore") or {}
    if not fs:
        return ""

    units_metric = fs.get("is_unitSystem_metric", True)
    weight_unit = "kg" if units_metric else "lb"
    height_unit = "cm" if units_metric else "in"

    fields: list[tuple[str, str]] = []

    # Demographics
    age = fs.get("age")
    gender = fs.get("gender")
    if age is not None or gender:
        bits = []
        if age is not None:
            bits.append(f"{age}")
        if gender:
            bits.append(_esc(gender))
        fields.append(("Demographics", " · ".join(bits) or "—"))

    # Height
    height = fs.get("height")
    if height is not None:
        fields.append(("Height", f"{_fmt_num(height)} <span class=\"secondary\">{height_unit}</span>"))

    # Weight (current vs target)
    cur = fs.get("current_weight") or fs.get("weight")
    target = fs.get("target_weight")
    if cur is not None or target is not None:
        bits = []
        if cur is not None:
            bits.append(f"{_fmt_num(cur)} {weight_unit}")
        if target is not None and target != cur:
            bits.append(f'<span class="secondary">→ {_fmt_num(target)} {weight_unit}</span>')
        fields.append(("Weight", " ".join(bits)))

    # Goal
    if fs.get("main_goal"):
        fields.append(("Main goal", _esc(fs["main_goal"])))

    # Activity
    if fs.get("activity_level"):
        fields.append(("Activity level", _esc(fs["activity_level"])))

    # Macro split
    p, c, f = fs.get("proteins"), fs.get("carbs"), fs.get("fats")
    if p is not None and c is not None and f is not None:
        fields.append((
            "Macro split",
            f"P {int(p*100)}% · C {int(c*100)}% · F {int(f*100)}%"
            if all(isinstance(v, (int, float)) and v <= 1 for v in (p, c, f))
            else f"P {p} · C {c} · F {f}",
        ))

    # Locale / Units
    tz = fs.get("timezone")
    if tz:
        units_str = "Metric" if units_metric else "Imperial"
        fields.append(("Locale", f"{_esc(tz)} <span class=\"secondary\">· {units_str}</span>"))

    # Activity dates
    created = fs.get("created_time")
    last_active = fs.get("last_active_timestamp")
    if created or last_active:
        bits = []
        if created:
            bits.append(f"joined {_fmt_fs_date(created)}")
        if last_active:
            bits.append(f'<span class="secondary">last active {_fmt_fs_date(last_active)}</span>')
        fields.append(("Activity", "<br>".join(bits)))

    # Onboarding flag
    if "Questionaries_was_completed" in fs:
        v = "yes" if fs["Questionaries_was_completed"] else "no"
        fields.append(("Onboarding done", v))

    if not fields:
        return ""

    cards = "".join(
        f'<div class="pf"><div class="pf-label">{label}</div>'
        f'<div class="pf-value">{value}</div></div>'
        for label, value in fields
    )
    return f'<div class="profile-section">{cards}</div>'


def _fmt_num(v) -> str:
    """Trim trailing zeros from floats: 70.30681735 → '70.3', 198.12 → '198.12'."""
    try:
        f = float(v)
        if f.is_integer():
            return str(int(f))
        return f"{f:.2f}".rstrip("0").rstrip(".")
    except Exception:
        return _esc(v)


def _fmt_fs_date(v) -> str:
    """Firestore returns ISO strings via json default=str."""
    if not v:
        return "—"
    s = str(v)
    # "2026-04-24 03:39:49.001000+00:00" → "2026-04-24"
    return _esc(s[:10] if len(s) >= 10 else s)


def _ident_cell(uid: str | None, type_: str, profile: dict | None) -> str:
    """Render name+email if we have profile; otherwise just the masked UID."""
    if type_ == "anon":
        return '<span class="uid-text" style="color:#64748b">(anonymous)</span>'
    if profile and (profile.get("display_name") or profile.get("email")):
        name = profile.get("display_name") or "—"
        email = profile.get("email") or ""
        return (
            f'<div class="ident-stack">'
            f'<div class="ident-name">{_esc(name)}</div>'
            f'<div class="ident-sub">{_esc(email)}</div>'
            f'</div>'
        )
    short = _user_short(uid, type_)
    return f'<span class="uid-text" title="{_esc(uid)}">{_esc(short)}</span>'


@router.post("/users/mobile/{uid}/refresh")
async def users_mobile_refresh(uid: str):
    """Synchronous refresh, then redirect back to detail."""
    await _refresh_mobile_profile(uid)
    return RedirectResponse(url=f"/users/mobile/{uid}", status_code=303)


@router.get("/users/anon", response_class=HTMLResponse)
async def users_anon_detail(
    range_: str | None = Query(None, alias="range"),
    date: str | None = Query(None),
):
    return await _render_user_detail("anon", None, range_, date)


@router.get("/users/{user_type}/{user_id}", response_class=HTMLResponse)
async def users_detail_page(
    user_type: str,
    user_id: str,
    range_: str | None = Query(None, alias="range"),
    date: str | None = Query(None),
):
    if user_type not in ("mobile", "tg"):
        raise HTTPException(status_code=404, detail="Unknown user type")
    return await _render_user_detail(user_type, user_id, range_, date)


async def _render_user_detail(
    user_type: str,
    user_id: str | None,
    range_: str | None,
    date: str | None = None,
) -> HTMLResponse:
    # Single-day filter takes precedence over range preset
    if date:
        rng = day_range(date)
        if rng:
            df, dt_end = rng
            active_preset = ""
        else:
            date = None  # invalid date — fall back to preset
            df, dt_end, active_preset, _, _ = resolve_range(range_, None, None)
    else:
        df, dt_end, active_preset, _, _ = resolve_range(range_, None, None)

    stats = await get_user_stats(user_type, user_id, date_from=df, date_to=dt_end)

    # Recent 50 scans for this user (no separate pagination yet)
    history = await get_user_history(user_type, user_id, limit=50, offset=0,
                                     date_from=df, date_to=dt_end)
    total_history = await count_user_history(user_type, user_id,
                                             date_from=df, date_to=dt_end)

    profile = None
    if user_type == "mobile" and user_id:
        profile = await _get_profile_with_refresh(user_id)

    profile_card_html = _profile_card_for(user_type, user_id, profile)
    title = _detail_title(user_type, user_id, profile)

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

    # by_day — rows clickable → History with date+user filters (visual scan list)
    base_path = (
        "/users/anon" if user_type == "anon"
        else f"/users/{user_type}/{user_id}"
    )
    # drill-down target: History view filtered to this day + this user
    def _day_drill_href(day: str) -> str:
        if user_type == "mobile":
            return f"/history/view/all?date={day}&mobile_user_id={user_id}"
        if user_type == "tg":
            return f"/history/view/all?date={day}&telegram_user_id={user_id}"
        # anon: just date filter
        return f"/history/view/all?date={day}"

    by_day = stats["by_day"]
    by_day_rows = ""
    if by_day:
        max_count = max(d["count"] for d in by_day) or 1
        for d in by_day:
            width = round(d["count"] / max_count * 100, 1)
            cost = f'${d["cost"]:.4f}' if d["cost"] else '—'
            href = _day_drill_href(d["day"])
            by_day_rows += (
                f'<tr class="clickable" onclick="location.href=\'{href}\'">'
                f'<td><strong>{d["day"]}</strong></td>'
                f'<td><div class="bar"><div class="bar-fill" style="width:{width}%"></div>'
                f'<span class="bar-num">{d["count"]}</span></div></td>'
                f'<td>{d["successes"]}</td>'
                f'<td>{cost}</td></tr>'
            )
    else:
        by_day_rows = '<tr><td colspan="4" class="empty">No data</td></tr>'

    # date filter banner (shown when ?date=YYYY-MM-DD is active)
    date_banner = ""
    if date:
        date_banner = (
            f'<div style="background:#1e293b;border:1px solid #38bdf8;border-radius:10px;'
            f'padding:10px 14px;margin-bottom:16px;color:#94a3b8;font-size:0.9em;'
            f'display:flex;align-items:center;gap:12px">'
            f'Showing for <strong style="color:#38bdf8">{_esc(date)}</strong> only — '
            f'all cards / Recent are scoped to this day.'
            f'<a href="{base_path}" style="color:#f87171;text-decoration:none;margin-left:auto;'
            f'padding:4px 10px;border-radius:6px;border:1px solid #334155;font-size:0.85em">'
            f'Clear day ✕</a></div>'
        )

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
{_firebase_status_banner()}
{profile_card_html}

{_filter_bar(active_preset) if not date else ""}
{date_banner}
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
