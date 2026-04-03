#!/usr/bin/env python3
"""
Show first N rows for all tables in public schema.

Usage:
  python scripts/show_all_tables_preview.py
  python scripts/show_all_tables_preview.py --limit 5
"""

import argparse
import asyncio
import sys
from pathlib import Path

from sqlalchemy import text

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal


async def show_all_tables_preview(limit: int) -> int:
    if limit <= 0:
        print("❌ Limit must be > 0")
        return 1

    async with AsyncSessionLocal() as db:
        tables_result = await db.execute(
            text(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
                """
            )
        )
        tables = [row[0] for row in tables_result.fetchall()]

        if not tables:
            print("⚠️ No tables found in public schema")
            return 0

        print(f"📚 Found {len(tables)} tables. Showing first {limit} rows each.\n")

        for table in tables:
            print(f"=== {table} ===")
            result = await db.execute(
                text(f'SELECT * FROM "{table}" LIMIT :limit'),
                {"limit": limit},
            )
            rows = result.fetchall()

            if not rows:
                print("(empty table)\n")
                continue

            for index, row in enumerate(rows, start=1):
                print(f"[{index}] {dict(row._mapping)}")
            print()

    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show first N rows for all tables")
    parser.add_argument("--limit", type=int, default=10, help="Number of rows (default: 10)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    exit_code = asyncio.run(show_all_tables_preview(limit=args.limit))
    sys.exit(exit_code)
