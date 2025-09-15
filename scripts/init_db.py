#!/usr/bin/env python3
"""
Database initialization script.
Creates all tables and optionally seeds with initial data.
"""
import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import AsyncSessionLocal
from app.core.graph_db import graph_db
from app.core.config import settings


async def init_database():
    """DEPRECATED: Use Alembic migrations instead."""
    print("⚠️  This script is deprecated. Use 'alembic upgrade head' for database migrations.")
    print("🔗 Testing database connections...")
    
    try:
        # Test PostgreSQL connection
        async with AsyncSessionLocal() as db:
            from sqlalchemy import text
            await db.execute(text("SELECT 1"))
        print("✅ PostgreSQL connection successful!")
        
        # Test Neo4j connection
        await graph_db.connect()
        async with graph_db.driver.session() as session:
            await session.run("RETURN 1")
        print("✅ Neo4j connection successful!")
        
        print("🎉 Database connections verified!")
        
    except Exception as e:
        print(f"❌ Error testing database connections: {e}")
        raise
    finally:
        await graph_db.close()


async def reset_database():
    """Reset the database by dropping and recreating all tables."""
    print("⚠️  Resetting database (this will delete all data)...")
    
    try:
        # Drop and recreate PostgreSQL tables
        print("🗑️  Dropping PostgreSQL tables...")
        async with engine.begin() as conn:
            from app.models import user, place, post, category, user_list
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        print("✅ PostgreSQL tables reset successfully!")
        
        # Clear Neo4j database
        print("🗑️  Clearing Neo4j database...")
        await graph_db.connect()
        async with graph_db.driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
        print("✅ Neo4j database cleared successfully!")
        
        # Seed initial data
        print("🌱 Seeding initial data...")
        await seed_initial_data()
        print("✅ Initial data seeded successfully!")
        
        print("🎉 Database reset completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during database reset: {e}")
        raise
    finally:
        await engine.dispose()
        await graph_db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database initialization script")
    parser.add_argument(
        "--reset", 
        action="store_true", 
        help="Reset database (drop all tables and data)"
    )
    
    args = parser.parse_args()
    
    if args.reset:
        confirm = input("Are you sure you want to reset the database? This will delete ALL data. (y/N): ")
        if confirm.lower() != 'y':
            print("Database reset cancelled.")
            sys.exit(0)
        asyncio.run(reset_database())
    else:
        asyncio.run(init_database())
