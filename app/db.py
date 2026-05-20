import json
import time
from pathlib import Path

import aiosqlite

DB_PATH = Path("data/stats.db")


async def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                response_time_ms INTEGER NOT NULL,
                success BOOLEAN NOT NULL,
                error TEXT,
                dish_name TEXT,
                image_size_bytes INTEGER,
                ingredients_count INTEGER,
                result_json TEXT,
                image_filename TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                cache_read_tokens INTEGER,
                cost_usd REAL,
                client_id INTEGER,
                telegram_user_id INTEGER,
                mobile_user_id TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                status TEXT NOT NULL DEFAULT 'active',
                created_at REAL NOT NULL,
                notes TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS mobile_users (
                uid TEXT PRIMARY KEY,
                email TEXT,
                display_name TEXT,
                photo_url TEXT,
                custom_claims_json TEXT,
                firestore_json TEXT,
                fetched_at REAL NOT NULL,
                fetch_error TEXT
            )
        """)
        # Migrations: add columns if missing (existing DBs)
        for column_def in [
            "ALTER TABLE requests ADD COLUMN result_json TEXT",
            "ALTER TABLE requests ADD COLUMN image_filename TEXT",
            "ALTER TABLE requests ADD COLUMN input_tokens INTEGER",
            "ALTER TABLE requests ADD COLUMN output_tokens INTEGER",
            "ALTER TABLE requests ADD COLUMN cache_read_tokens INTEGER",
            "ALTER TABLE requests ADD COLUMN cost_usd REAL",
            "ALTER TABLE requests ADD COLUMN client_id INTEGER",
            "ALTER TABLE requests ADD COLUMN telegram_user_id INTEGER",
            "ALTER TABLE requests ADD COLUMN mobile_user_id TEXT",
        ]:
            try:
                await db.execute(column_def)
            except Exception:
                pass  # column already exists
        await db.commit()


async def log_request(
    *,
    provider: str,
    model: str,
    response_time_ms: int,
    success: bool,
    error: str | None = None,
    dish_name: str | None = None,
    image_size_bytes: int | None = None,
    ingredients_count: int | None = None,
    result_json: dict | None = None,
    image_filename: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
    cache_read_tokens: int | None = None,
    cost_usd: float | None = None,
    client_id: int | None = None,
    telegram_user_id: int | None = None,
    mobile_user_id: str | None = None,
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO requests
               (timestamp, provider, model, response_time_ms, success, error,
                dish_name, image_size_bytes, ingredients_count, result_json, image_filename,
                input_tokens, output_tokens, cache_read_tokens, cost_usd,
                client_id, telegram_user_id, mobile_user_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                time.time(), provider, model, response_time_ms, success,
                error, dish_name, image_size_bytes, ingredients_count,
                json.dumps(result_json, ensure_ascii=False) if result_json else None,
                image_filename,
                input_tokens, output_tokens, cache_read_tokens, cost_usd,
                client_id, telegram_user_id, mobile_user_id,
            ),
        )
        await db.commit()
        return cursor.lastrowid


async def get_client_by_token_hash(token_hash: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, name, status FROM clients WHERE token_hash = ? AND status = 'active'",
            (token_hash,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None


async def list_clients() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, name, status, created_at, notes FROM clients ORDER BY id"
        )
        return [dict(row) for row in await cursor.fetchall()]


async def add_client(name: str, token_hash: str, notes: str | None = None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO clients (name, token_hash, status, created_at, notes) VALUES (?, ?, 'active', ?, ?)",
            (name, token_hash, time.time(), notes),
        )
        await db.commit()
        return cursor.lastrowid


async def set_client_status(client_id: int, status: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE clients SET status = ? WHERE id = ?",
            (status, client_id),
        )
        await db.commit()


def _range_clause(date_from: float | None, date_to: float | None) -> tuple[str, list]:
    parts, params = [], []
    if date_from is not None:
        parts.append("timestamp >= ?")
        params.append(date_from)
    if date_to is not None:
        parts.append("timestamp < ?")
        params.append(date_to)
    return (" AND " + " AND ".join(parts) if parts else ""), params


async def get_stats(
    date_from: float | None = None,
    date_to: float | None = None,
) -> dict:
    where_extra, params = _range_clause(date_from, date_to)
    base_where = "1=1" + where_extra

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(f"SELECT COUNT(*) FROM requests WHERE {base_where}", params)
        total = (await cursor.fetchone())[0]

        cursor = await db.execute(
            f"SELECT COUNT(*) FROM requests WHERE success = 1 AND {base_where}", params
        )
        success_count = (await cursor.fetchone())[0]

        cursor = await db.execute(
            f"""SELECT provider, model, COUNT(*) as count,
                       ROUND(AVG(response_time_ms)) as avg_time_ms,
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
                       COALESCE(SUM(input_tokens), 0) as input_tokens,
                       COALESCE(SUM(output_tokens), 0) as output_tokens,
                       COALESCE(SUM(cost_usd), 0) as cost_usd
                FROM requests WHERE {base_where}
                GROUP BY provider, model
                ORDER BY count DESC""",
            params,
        )
        by_provider = [dict(row) for row in await cursor.fetchall()]

        cursor = await db.execute(
            f"""SELECT timestamp, provider, model, response_time_ms,
                       success, error, dish_name, ingredients_count,
                       mobile_user_id, telegram_user_id, cost_usd
                FROM requests WHERE {base_where}
                ORDER BY timestamp DESC LIMIT 20""",
            params,
        )
        recent = [dict(row) for row in await cursor.fetchall()]

        cursor = await db.execute(
            f"SELECT ROUND(AVG(response_time_ms)) FROM requests WHERE success = 1 AND {base_where}",
            params,
        )
        avg_time = (await cursor.fetchone())[0] or 0

        cursor = await db.execute(
            f"""SELECT DATE(timestamp, 'unixepoch', 'localtime') as day,
                       COUNT(*) as count,
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
                       ROUND(AVG(response_time_ms)) as avg_time_ms,
                       COALESCE(SUM(input_tokens), 0) as input_tokens,
                       COALESCE(SUM(output_tokens), 0) as output_tokens,
                       COALESCE(SUM(cost_usd), 0) as cost_usd,
                       COUNT(DISTINCT COALESCE(
                           mobile_user_id,
                           'tg:' || CAST(telegram_user_id AS TEXT),
                           'anon'
                       )) as unique_users
                FROM requests WHERE {base_where}
                GROUP BY day
                ORDER BY day DESC""",
            params,
        )
        by_day = [dict(row) for row in await cursor.fetchall()]

        cursor = await db.execute(
            f"""SELECT
                  COALESCE(SUM(input_tokens), 0) as input_tokens,
                  COALESCE(SUM(output_tokens), 0) as output_tokens,
                  COALESCE(SUM(cache_read_tokens), 0) as cache_read_tokens,
                  COALESCE(SUM(cost_usd), 0) as cost_usd,
                  SUM(CASE WHEN cost_usd IS NULL THEN 1 ELSE 0 END) as without_cost
                FROM requests WHERE {base_where}""",
            params,
        )
        totals = dict(await cursor.fetchone())

        cursor = await db.execute(
            f"""SELECT
                  SUM(CASE WHEN client_id IS NULL THEN 1 ELSE 0 END) as anon,
                  SUM(CASE WHEN client_id IS NOT NULL THEN 1 ELSE 0 END) as known
                FROM requests WHERE {base_where}""",
            params,
        )
        client_split = dict(await cursor.fetchone())

    days_active = len(by_day)
    avg_per_day = round(total / days_active, 1) if days_active else 0
    peak = max(by_day, key=lambda d: d["count"]) if by_day else None

    avg_cost = round(totals["cost_usd"] / total, 4) if total > 0 and totals["cost_usd"] else 0
    cost_per_day = round(totals["cost_usd"] / days_active, 4) if days_active and totals["cost_usd"] else 0
    anon_pct = round(client_split["anon"] / total * 100, 1) if total > 0 else 0

    return {
        "total_requests": total,
        "successful": success_count,
        "failed": total - success_count,
        "success_rate": round(success_count / total * 100, 1) if total > 0 else 0,
        "avg_response_time_ms": int(avg_time),
        "by_provider_model": by_provider,
        "recent_requests": recent,
        "by_day": by_day,
        "days_active": days_active,
        "avg_per_day": avg_per_day,
        "peak_day": peak,
        "total_input_tokens": int(totals["input_tokens"]),
        "total_output_tokens": int(totals["output_tokens"]),
        "total_cache_read_tokens": int(totals["cache_read_tokens"]),
        "total_cost_usd": round(totals["cost_usd"], 4),
        "without_cost_count": int(totals["without_cost"]),
        "avg_cost_usd": avg_cost,
        "cost_per_day": cost_per_day,
        "anon_count": int(client_split["anon"]),
        "known_count": int(client_split["known"]),
        "anon_pct": anon_pct,
    }


def _status_clause(status: str) -> str:
    if status == "failed":
        return " AND success = 0"
    if status == "all":
        return ""
    return " AND success = 1 AND result_json IS NOT NULL"


def _user_filter_clause(
    mobile_user_id: str | None,
    telegram_user_id: int | None,
) -> tuple[str, list]:
    """Build extra WHERE + params for narrowing history to a specific user."""
    parts, params = [], []
    if mobile_user_id:
        parts.append("mobile_user_id = ?")
        params.append(mobile_user_id)
    if telegram_user_id is not None:
        parts.append("telegram_user_id = ?")
        params.append(telegram_user_id)
    return (" AND " + " AND ".join(parts) if parts else ""), params


async def count_history(
    date_from: float | None = None,
    date_to: float | None = None,
    status: str = "success",
    mobile_user_id: str | None = None,
    telegram_user_id: int | None = None,
) -> int:
    where_extra, params = _range_clause(date_from, date_to)
    user_extra, user_params = _user_filter_clause(mobile_user_id, telegram_user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            f"""SELECT COUNT(*) FROM requests
                WHERE 1=1{_status_clause(status)}{where_extra}{user_extra}""",
            params + user_params,
        )
        return (await cursor.fetchone())[0]


async def count_history_by_status(
    date_from: float | None = None,
    date_to: float | None = None,
    mobile_user_id: str | None = None,
    telegram_user_id: int | None = None,
) -> dict:
    """Returns {"success": N, "failed": M} for the date range (optionally per-user)."""
    where_extra, params = _range_clause(date_from, date_to)
    user_extra, user_params = _user_filter_clause(mobile_user_id, telegram_user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            f"""SELECT
                  SUM(CASE WHEN success = 1 AND result_json IS NOT NULL THEN 1 ELSE 0 END) as success,
                  SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed
                FROM requests WHERE 1=1{where_extra}{user_extra}""",
            params + user_params,
        )
        row = await cursor.fetchone()
    return {"success": row[0] or 0, "failed": row[1] or 0}


async def get_history(
    limit: int = 100,
    offset: int = 0,
    date_from: float | None = None,
    date_to: float | None = None,
    status: str = "success",
    mobile_user_id: str | None = None,
    telegram_user_id: int | None = None,
) -> list[dict]:
    where_extra, params = _range_clause(date_from, date_to)
    user_extra, user_params = _user_filter_clause(mobile_user_id, telegram_user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            f"""SELECT id, timestamp, provider, model, response_time_ms,
                       success, error, dish_name, ingredients_count,
                       result_json, image_filename,
                       input_tokens, output_tokens, cache_read_tokens, cost_usd,
                       client_id, telegram_user_id, mobile_user_id
                FROM requests
                WHERE 1=1{_status_clause(status)}{where_extra}{user_extra}
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?""",
            (*params, *user_params, limit, offset),
        )
        rows = []
        for row in await cursor.fetchall():
            entry = dict(row)
            if entry.get("result_json"):
                entry["result"] = json.loads(entry["result_json"])
            entry.pop("result_json", None)
            rows.append(entry)
        return rows


async def get_entry(entry_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT id, timestamp, provider, model, response_time_ms,
                      dish_name, ingredients_count, result_json, image_filename,
                      input_tokens, output_tokens, cache_read_tokens, cost_usd,
                      client_id, telegram_user_id, mobile_user_id
               FROM requests WHERE id = ?""",
            (entry_id,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        entry = dict(row)
        if entry["result_json"]:
            entry["result"] = json.loads(entry["result_json"])
            del entry["result_json"]
        return entry


async def update_image_filename(entry_id: int, filename: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE requests SET image_filename = ? WHERE id = ?",
            (filename, entry_id),
        )
        await db.commit()


# ---------------------------------------------------------------------------
# Users (mobile via mobile_user_id; telegram via telegram_user_id; anon)
# ---------------------------------------------------------------------------

def _user_predicate(user_type: str) -> str:
    """SQL fragment to match the bucket. Use placeholders only when needed."""
    if user_type == "mobile":
        return "mobile_user_id = ?"
    if user_type == "tg":
        return "telegram_user_id = ?"
    if user_type == "anon":
        return "mobile_user_id IS NULL AND telegram_user_id IS NULL"
    raise ValueError(f"Unknown user_type: {user_type}")


async def list_users(
    date_from: float | None = None,
    date_to: float | None = None,
    limit: int = 200,
) -> list[dict]:
    """Return aggregated user list across mobile, telegram, anonymous."""
    where_extra, params = _range_clause(date_from, date_to)

    rows: list[dict] = []
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Mobile users
        cursor = await db.execute(
            f"""SELECT mobile_user_id as uid,
                       COUNT(*) as total,
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
                       COALESCE(SUM(cost_usd), 0) as cost,
                       MIN(timestamp) as first_ts,
                       MAX(timestamp) as last_ts
                FROM requests
                WHERE mobile_user_id IS NOT NULL{where_extra}
                GROUP BY mobile_user_id
                ORDER BY total DESC
                LIMIT ?""",
            (*params, limit),
        )
        for r in await cursor.fetchall():
            d = dict(r)
            d["type"] = "mobile"
            rows.append(d)

        # Telegram users
        cursor = await db.execute(
            f"""SELECT CAST(telegram_user_id as TEXT) as uid,
                       COUNT(*) as total,
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
                       COALESCE(SUM(cost_usd), 0) as cost,
                       MIN(timestamp) as first_ts,
                       MAX(timestamp) as last_ts
                FROM requests
                WHERE telegram_user_id IS NOT NULL{where_extra}
                GROUP BY telegram_user_id
                ORDER BY total DESC
                LIMIT ?""",
            (*params, limit),
        )
        for r in await cursor.fetchall():
            d = dict(r)
            d["type"] = "tg"
            rows.append(d)

        # Anonymous bucket (one synthetic row)
        cursor = await db.execute(
            f"""SELECT COUNT(*) as total,
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
                       COALESCE(SUM(cost_usd), 0) as cost,
                       MIN(timestamp) as first_ts,
                       MAX(timestamp) as last_ts
                FROM requests
                WHERE mobile_user_id IS NULL AND telegram_user_id IS NULL{where_extra}""",
            params,
        )
        r = await cursor.fetchone()
        if r and (r["total"] or 0) > 0:
            rows.append({
                "type": "anon",
                "uid": "—",
                "total": r["total"],
                "successes": r["successes"] or 0,
                "cost": r["cost"] or 0,
                "first_ts": r["first_ts"],
                "last_ts": r["last_ts"],
            })

    return rows


async def get_user_stats(
    user_type: str,
    user_id: str | None,
    date_from: float | None = None,
    date_to: float | None = None,
) -> dict:
    """Aggregated stats for a single user (or anonymous bucket)."""
    where_extra, range_params = _range_clause(date_from, date_to)
    pred = _user_predicate(user_type)
    params = ([user_id] if user_type != "anon" else []) + list(range_params)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute(
            f"""SELECT COUNT(*) as total,
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
                       SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed,
                       COALESCE(SUM(cost_usd), 0) as total_cost,
                       COALESCE(SUM(input_tokens), 0) as input_tokens,
                       COALESCE(SUM(output_tokens), 0) as output_tokens,
                       MIN(timestamp) as first_ts,
                       MAX(timestamp) as last_ts,
                       ROUND(AVG(response_time_ms)) as avg_response_ms
                FROM requests
                WHERE {pred}{where_extra}""",
            params,
        )
        totals = dict(await cursor.fetchone())

        cursor = await db.execute(
            f"""SELECT DATE(timestamp, 'unixepoch', 'localtime') as day,
                       COUNT(*) as count,
                       SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes,
                       COALESCE(SUM(cost_usd), 0) as cost
                FROM requests
                WHERE {pred}{where_extra}
                GROUP BY day
                ORDER BY day DESC""",
            params,
        )
        by_day = [dict(r) for r in await cursor.fetchall()]

        cursor = await db.execute(
            f"""SELECT provider, model,
                       COUNT(*) as count,
                       COALESCE(SUM(cost_usd), 0) as cost
                FROM requests
                WHERE {pred}{where_extra}
                GROUP BY provider, model
                ORDER BY count DESC""",
            params,
        )
        by_provider = [dict(r) for r in await cursor.fetchall()]

    total = totals.get("total") or 0
    days_active = len(by_day)
    return {
        "total": total,
        "successes": totals.get("successes") or 0,
        "failed": totals.get("failed") or 0,
        "success_rate": round((totals["successes"] or 0) / total * 100, 1) if total else 0,
        "total_cost": round(totals.get("total_cost") or 0, 4),
        "input_tokens": int(totals.get("input_tokens") or 0),
        "output_tokens": int(totals.get("output_tokens") or 0),
        "first_ts": totals.get("first_ts"),
        "last_ts": totals.get("last_ts"),
        "avg_response_ms": int(totals.get("avg_response_ms") or 0),
        "days_active": days_active,
        "avg_per_day": round(total / days_active, 1) if days_active else 0,
        "by_day": by_day,
        "by_provider": by_provider,
    }


async def get_user_history(
    user_type: str,
    user_id: str | None,
    limit: int = 100,
    offset: int = 0,
    date_from: float | None = None,
    date_to: float | None = None,
) -> list[dict]:
    where_extra, range_params = _range_clause(date_from, date_to)
    pred = _user_predicate(user_type)
    params = ([user_id] if user_type != "anon" else []) + list(range_params) + [limit, offset]

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            f"""SELECT id, timestamp, provider, model, response_time_ms,
                       success, error, dish_name, ingredients_count,
                       result_json, image_filename,
                       input_tokens, output_tokens, cost_usd
                FROM requests
                WHERE {pred}{where_extra}
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?""",
            params,
        )
        rows = []
        for row in await cursor.fetchall():
            entry = dict(row)
            if entry.get("result_json"):
                entry["result"] = json.loads(entry["result_json"])
            entry.pop("result_json", None)
            rows.append(entry)
        return rows


async def count_user_history(
    user_type: str,
    user_id: str | None,
    date_from: float | None = None,
    date_to: float | None = None,
) -> int:
    where_extra, range_params = _range_clause(date_from, date_to)
    pred = _user_predicate(user_type)
    params = ([user_id] if user_type != "anon" else []) + list(range_params)

    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            f"SELECT COUNT(*) FROM requests WHERE {pred}{where_extra}",
            params,
        )
        return (await cursor.fetchone())[0]


# ---------------------------------------------------------------------------
# Mobile user profile cache (Firebase Auth + Firestore snapshot)
# ---------------------------------------------------------------------------

async def get_cached_mobile_user(uid: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM mobile_users WHERE uid = ?", (uid,),
        )
        row = await cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        if d.get("custom_claims_json"):
            try:
                d["custom_claims"] = json.loads(d["custom_claims_json"])
            except Exception:
                d["custom_claims"] = {}
        else:
            d["custom_claims"] = {}
        if d.get("firestore_json"):
            try:
                d["firestore"] = json.loads(d["firestore_json"])
            except Exception:
                d["firestore"] = None
        else:
            d["firestore"] = None
        return d


async def get_cached_mobile_users(uids: list[str]) -> dict[str, dict]:
    """Batch fetch — returns {uid: profile_dict}."""
    if not uids:
        return {}
    placeholders = ",".join("?" * len(uids))
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            f"SELECT * FROM mobile_users WHERE uid IN ({placeholders})", uids,
        )
        out = {}
        for row in await cursor.fetchall():
            d = dict(row)
            out[d["uid"]] = d
        return out


async def upsert_mobile_user(uid: str, profile: dict | None, error: str | None = None) -> None:
    """Insert or replace the cached profile. `profile` can be None on hard-fail."""
    custom_claims_json = None
    firestore_json = None
    email = display_name = photo_url = None

    if profile:
        email = profile.get("email")
        display_name = profile.get("display_name")
        photo_url = profile.get("photo_url")
        if profile.get("custom_claims"):
            custom_claims_json = json.dumps(profile["custom_claims"], ensure_ascii=False)
        if profile.get("firestore") is not None:
            firestore_json = json.dumps(profile["firestore"], ensure_ascii=False, default=str)
        # propagate per-source errors into a single fetch_error if both Auth+Firestore failed
        if not error:
            a_err = profile.get("_auth_error")
            f_err = profile.get("_firestore_error")
            if a_err and f_err:
                error = f"auth:{a_err}; firestore:{f_err}"
            elif a_err:
                error = f"auth:{a_err}"
            elif f_err:
                error = f"firestore:{f_err}"

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO mobile_users
                 (uid, email, display_name, photo_url, custom_claims_json,
                  firestore_json, fetched_at, fetch_error)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(uid) DO UPDATE SET
                 email = excluded.email,
                 display_name = excluded.display_name,
                 photo_url = excluded.photo_url,
                 custom_claims_json = excluded.custom_claims_json,
                 firestore_json = excluded.firestore_json,
                 fetched_at = excluded.fetched_at,
                 fetch_error = excluded.fetch_error""",
            (
                uid, email, display_name, photo_url, custom_claims_json,
                firestore_json, time.time(), error,
            ),
        )
        await db.commit()


async def mobile_user_cache_stale(uid: str, ttl_sec: int) -> bool:
    """Return True if there is no cache row or it is older than ttl_sec."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT fetched_at FROM mobile_users WHERE uid = ?", (uid,),
        )
        row = await cursor.fetchone()
        if not row:
            return True
        return (time.time() - row[0]) > ttl_sec
