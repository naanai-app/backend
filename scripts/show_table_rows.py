#!/usr/bin/env python3
"""
Show first N rows from a specific PostgreSQL table.

Usage:
  python scripts/show_table_rows.py --table users
  python scripts/show_table_rows.py --table places --limit 20
"""

import argparse
import asyncio
import re
import sys
from pathlib import Path

from sqlalchemy import text

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _is_valid_identifier(value: str) -> bool:
    return bool(_IDENTIFIER_RE.match(value))


async def show_table_rows(table: str, limit: int) -> int:
    if not _is_valid_identifier(table):
        print(f"❌ Invalid table name: {table}")
        return 1

    if limit <= 0:
        print("❌ Limit must be > 0")
        return 1

    async with AsyncSessionLocal() as db:
        table_exists_result = await db.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = :table_name
                )
                """
            ),
            {"table_name": table},
        )
        table_exists = table_exists_result.scalar_one()

        if not table_exists:
            print(f"❌ Table not found in public schema: {table}")
            return 1

        query = text(f'SELECT * FROM "{table}" LIMIT :limit')
        result = await db.execute(query, {"limit": limit})
        rows = result.fetchall()

        print(f"\n📋 Table: {table}")
        print(f"🔢 Rows returned: {len(rows)} (limit={limit})")

        if not rows:
            print("(empty table)")
            return 0

        for index, row in enumerate(rows, start=1):
            print(f"\n[{index}] {dict(row._mapping)}")

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show first N rows from a table")
    parser.add_argument("--table", required=True, help="Table name in public schema")
    parser.add_argument("--limit", type=int, default=10, help="Number of rows (default: 10)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    exit_code = asyncio.run(show_table_rows(table=args.table, limit=args.limit))
    sys.exit(exit_code)
