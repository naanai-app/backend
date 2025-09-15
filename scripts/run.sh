#!/bin/bash
# Convenience script to run common database operations

set -e

case "$1" in
    "init")
        echo "🚀 Initializing database..."
        python scripts/init_db.py
        ;;
    "reset")
        echo "⚠️  Resetting database..."
        python scripts/init_db.py --reset
        ;;
    "check")
        echo "🔍 Checking database health..."
        python scripts/check_db.py
        ;;
    "seed")
        echo "🌱 Seeding data..."
        python scripts/seed_data.py
        ;;
    "admin")
        echo "👤 Creating admin user..."
        python scripts/create_admin.py
        ;;
    "dev")
        echo "🚀 Starting development server..."
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
        ;;
    *)
        echo "Usage: $0 {init|reset|check|seed|admin|dev}"
        echo ""
        echo "Commands:"
        echo "  init   - Initialize database tables"
        echo "  reset  - Reset database (WARNING: deletes all data)"
        echo "  check  - Check database connections"
        echo "  seed   - Seed initial data"
        echo "  admin  - Create admin user"
        echo "  dev    - Start development server"
        exit 1
        ;;
esac
