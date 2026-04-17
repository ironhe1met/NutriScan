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
                image_filename TEXT
            )
        """)
        # Migrations: add columns if missing (existing DBs)
        for column_def in [
            "ALTER TABLE requests ADD COLUMN result_json TEXT",
            "ALTER TABLE requests ADD COLUMN image_filename TEXT",
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
) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """INSERT INTO requests
               (timestamp, provider, model, response_time_ms, success, error,
                dish_name, image_size_bytes, ingredients_count, result_json, image_filename)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                time.time(), provider, model, response_time_ms, success,
                error, dish_name, image_size_bytes, ingredients_count,
                json.dumps(result_json, ensure_ascii=False) if result_json else None,
                image_filename,
            ),
        )
        await db.commit()
        return cursor.lastrowid


async def get_stats() -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        cursor = await db.execute("SELECT COUNT(*) FROM requests")
        total = (await cursor.fetchone())[0]

        cursor = await db.execute("SELECT COUNT(*) FROM requests WHERE success = 1")
        success_count = (await cursor.fetchone())[0]

        cursor = await db.execute(
            """SELECT provider, model, COUNT(*) as count,
                      ROUND(AVG(response_time_ms)) as avg_time_ms,
                      SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes
               FROM requests GROUP BY provider, model"""
        )
        by_provider = [dict(row) for row in await cursor.fetchall()]

        cursor = await db.execute(
            """SELECT timestamp, provider, model, response_time_ms,
                      success, error, dish_name, ingredients_count
               FROM requests ORDER BY timestamp DESC LIMIT 20"""
        )
        recent = [dict(row) for row in await cursor.fetchall()]

        cursor = await db.execute(
            "SELECT ROUND(AVG(response_time_ms)) FROM requests WHERE success = 1"
        )
        avg_time = (await cursor.fetchone())[0] or 0

    return {
        "total_requests": total,
        "successful": success_count,
        "failed": total - success_count,
        "success_rate": round(success_count / total * 100, 1) if total > 0 else 0,
        "avg_response_time_ms": int(avg_time),
        "by_provider_model": by_provider,
        "recent_requests": recent,
    }


async def count_history() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT COUNT(*) FROM requests WHERE success = 1 AND result_json IS NOT NULL"
        )
        return (await cursor.fetchone())[0]


async def get_history(limit: int = 100, offset: int = 0) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT id, timestamp, provider, model, response_time_ms,
                      dish_name, ingredients_count, result_json, image_filename
               FROM requests
               WHERE success = 1 AND result_json IS NOT NULL
               ORDER BY timestamp DESC
               LIMIT ? OFFSET ?""",
            (limit, offset),
        )
        rows = []
        for row in await cursor.fetchall():
            entry = dict(row)
            if entry["result_json"]:
                entry["result"] = json.loads(entry["result_json"])
                del entry["result_json"]
            rows.append(entry)
        return rows


async def get_entry(entry_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT id, timestamp, provider, model, response_time_ms,
                      dish_name, ingredients_count, result_json, image_filename
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
