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
                telegram_user_id INTEGER
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
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO requests
               (timestamp, provider, model, response_time_ms, success, error,
                dish_name, image_size_bytes, ingredients_count, result_json, image_filename,
                input_tokens, output_tokens, cache_read_tokens, cost_usd,
                client_id, telegram_user_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                time.time(), provider, model, response_time_ms, success,
                error, dish_name, image_size_bytes, ingredients_count,
                json.dumps(result_json, ensure_ascii=False) if result_json else None,
                image_filename,
                input_tokens, output_tokens, cache_read_tokens, cost_usd,
                client_id, telegram_user_id,
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
                       success, error, dish_name, ingredients_count
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
                       COALESCE(SUM(cost_usd), 0) as cost_usd
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


async def count_history(
    date_from: float | None = None,
    date_to: float | None = None,
    status: str = "success",
) -> int:
    where_extra, params = _range_clause(date_from, date_to)
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            f"""SELECT COUNT(*) FROM requests
                WHERE 1=1{_status_clause(status)}{where_extra}""",
            params,
        )
        return (await cursor.fetchone())[0]


async def count_history_by_status(
    date_from: float | None = None,
    date_to: float | None = None,
) -> dict:
    """Returns {"success": N, "failed": M} for the date range."""
    where_extra, params = _range_clause(date_from, date_to)
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            f"""SELECT
                  SUM(CASE WHEN success = 1 AND result_json IS NOT NULL THEN 1 ELSE 0 END) as success,
                  SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed
                FROM requests WHERE 1=1{where_extra}""",
            params,
        )
        row = await cursor.fetchone()
    return {"success": row[0] or 0, "failed": row[1] or 0}


async def get_history(
    limit: int = 100,
    offset: int = 0,
    date_from: float | None = None,
    date_to: float | None = None,
    status: str = "success",
) -> list[dict]:
    where_extra, params = _range_clause(date_from, date_to)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            f"""SELECT id, timestamp, provider, model, response_time_ms,
                       success, error, dish_name, ingredients_count,
                       result_json, image_filename,
                       input_tokens, output_tokens, cache_read_tokens, cost_usd,
                       client_id, telegram_user_id
                FROM requests
                WHERE 1=1{_status_clause(status)}{where_extra}
                ORDER BY timestamp DESC
                LIMIT ? OFFSET ?""",
            (*params, limit, offset),
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
                      client_id, telegram_user_id
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
