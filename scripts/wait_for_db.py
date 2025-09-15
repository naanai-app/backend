#!/usr/bin/env python3
"""
Wait for database services to be ready before starting the application.
"""
import asyncio
import sys
import time
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from app.core.graph_db import graph_db
from sqlalchemy import text


async def wait_for_postgresql(max_retries=30, delay=2):
    """Wait for PostgreSQL to be ready."""
    print("⏳ Waiting for PostgreSQL...")
    
    for attempt in range(max_retries):
        try:
            async with AsyncSessionLocal() as db:
                await db.execute(text("SELECT 1"))
            print("✅ PostgreSQL is ready!")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"   Attempt {attempt + 1}/{max_retries} failed: {e}")
                await asyncio.sleep(delay)
            else:
                print(f"❌ PostgreSQL not ready after {max_retries} attempts")
                return False
    
    return False


async def wait_for_neo4j(max_retries=30, delay=2):
    """Wait for Neo4j to be ready."""
    print("⏳ Waiting for Neo4j...")
    
    for attempt in range(max_retries):
        try:
            await graph_db.connect()
            async with graph_db.driver.session() as session:
                await session.run("RETURN 1")
            print("✅ Neo4j is ready!")
            await graph_db.close()
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"   Attempt {attempt + 1}/{max_retries} failed: {e}")
                await asyncio.sleep(delay)
            else:
                print(f"❌ Neo4j not ready after {max_retries} attempts")
                return False
        finally:
            try:
                await graph_db.close()
            except:
                pass
    
    return False


async def wait_for_databases():
    """Wait for all databases to be ready."""
    print("🔄 Waiting for database services to be ready...")
    
    postgresql_ready = await wait_for_postgresql()
    neo4j_ready = await wait_for_neo4j()
    
    if postgresql_ready and neo4j_ready:
        print("🎉 All database services are ready!")
        return True
    else:
        print("❌ Some database services failed to start")
        return False


if __name__ == "__main__":
    success = asyncio.run(wait_for_databases())
    sys.exit(0 if success else 1)
