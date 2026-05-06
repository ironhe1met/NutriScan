#!/usr/bin/env python
"""Manage API clients (clients table) — add, list, disable.

Usage:
    python -m scripts.manage_clients add  <name> [--notes "..."]
    python -m scripts.manage_clients list
    python -m scripts.manage_clients disable <id>
    python -m scripts.manage_clients enable  <id>

Run from project root with venv activated:
    venv/bin/python -m scripts.manage_clients add BroCalories --notes "Android, Google Play"

Token is generated and shown ONCE. Save it — we store only sha256(token).
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import secrets
import sys
from datetime import datetime

from app.db import init_db, add_client, list_clients, set_client_status


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


async def cmd_add(name: str, notes: str | None) -> int:
    await init_db()
    token = _generate_token()
    cid = await add_client(name=name, token_hash=_hash(token), notes=notes)
    print(f"✓ Client '{name}' added with id={cid}")
    print()
    print("⚠️  Save this token NOW — it is shown only once and stored only as sha256:")
    print()
    print(f"    {token}")
    print()
    print("Set on the client side as:")
    print(f"    Authorization: Bearer {token}")
    return cid


async def cmd_list() -> None:
    await init_db()
    rows = await list_clients()
    if not rows:
        print("(no clients)")
        return
    print(f"{'id':>4}  {'status':10}  {'name':30}  {'created':19}  notes")
    print("-" * 90)
    for r in rows:
        ts = datetime.fromtimestamp(r["created_at"]).strftime("%Y-%m-%d %H:%M:%S")
        print(f"{r['id']:>4}  {r['status']:10}  {r['name']:30}  {ts}  {r.get('notes') or ''}")


async def cmd_set_status(client_id: int, status: str) -> None:
    await init_db()
    await set_client_status(client_id, status)
    print(f"✓ Client id={client_id} → status='{status}'")


def main() -> int:
    parser = argparse.ArgumentParser(prog="manage_clients")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add = sub.add_parser("add", help="Add a new client + generate API token")
    p_add.add_argument("name")
    p_add.add_argument("--notes", default=None)

    sub.add_parser("list", help="List all clients")

    p_dis = sub.add_parser("disable", help="Set status='disabled'")
    p_dis.add_argument("id", type=int)

    p_en = sub.add_parser("enable", help="Set status='active'")
    p_en.add_argument("id", type=int)

    args = parser.parse_args()

    if args.cmd == "add":
        asyncio.run(cmd_add(args.name, args.notes))
    elif args.cmd == "list":
        asyncio.run(cmd_list())
    elif args.cmd == "disable":
        asyncio.run(cmd_set_status(args.id, "disabled"))
    elif args.cmd == "enable":
        asyncio.run(cmd_set_status(args.id, "active"))

    return 0


if __name__ == "__main__":
    sys.exit(main())
