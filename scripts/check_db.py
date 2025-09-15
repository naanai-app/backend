#!/usr/bin/env python3
"""
Database health check script.
Verifies database connections and table status.
"""
import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import engine, AsyncSessionLocal
from app.core.graph_db import graph_db
from app.core.config import settings
from sqlalchemy import text


async def check_postgresql():
    """Check PostgreSQL connection and tables."""
    print("🔍 Checking PostgreSQL connection...")
    
    try:
        async with AsyncSessionLocal() as db:
            # Test connection
            result = await db.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ PostgreSQL connected: {version}")
            
            # Check tables
            result = await db.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print(f"✅ Found {len(tables)} tables: {', '.join(tables)}")
            else:
                print("⚠️  No tables found. Run 'python scripts/init_db.py' to create tables.")
            
            return True
            
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False


async def check_neo4j():
    """Check Neo4j connection and basic functionality."""
    print("🔍 Checking Neo4j connection...")
    
    try:
        await graph_db.connect()
        
        # Test connection with a simple query
        async with graph_db.driver.session() as session:
            result = await session.run("RETURN 'Hello Neo4j' as message")
            record = await result.single()
            message = record["message"]
            print(f"✅ Neo4j connected: {message}")
            
            # Check if there are any nodes
            result = await session.run("MATCH (n) RETURN count(n) as count")
            record = await result.single()
            node_count = record["count"]
            print(f"✅ Neo4j has {node_count} nodes")
            
        return True
        
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        return False
    finally:
        await graph_db.close()


async def check_database_health():
    """Run comprehensive database health check."""
    print("🏥 Running database health check...")
    print(f"📋 Configuration:")
    print(f"   - PostgreSQL: {settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}")
    print(f"   - Neo4j: {settings.NEO4J_URI}")
    print()
    
    postgresql_ok = await check_postgresql()
    neo4j_ok = await check_neo4j()
    
    print()
    if postgresql_ok and neo4j_ok:
        print("🎉 All database connections are healthy!")
        return True
    else:
        print("❌ Some database connections failed. Check your configuration and ensure services are running.")
        return False


if __name__ == "__main__":
    success = asyncio.run(check_database_health())
    sys.exit(0 if success else 1)
