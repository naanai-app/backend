#!/usr/bin/env python3
"""
Database migration script using Alembic.
"""
import subprocess
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))


def run_migrations():
    """Run Alembic migrations."""
    try:
        print("📊 Running database migrations...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Database migrations completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def create_migration(message: str):
    """Create a new migration."""
    try:
        print(f"📝 Creating migration: {message}")
        result = subprocess.run(
            ["alembic", "revision", "--autogenerate", "-m", message],
            check=True,
            capture_output=True,
            text=True
        )
        print("✅ Migration created successfully!")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration creation failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Database migration script")
    parser.add_argument(
        "--create", 
        type=str,
        help="Create a new migration with the given message"
    )
    
    args = parser.parse_args()
    
    if args.create:
        success = create_migration(args.create)
    else:
        success = run_migrations()
    
    sys.exit(0 if success else 1)
