#!/bin/bash
# Docker entrypoint script for production-ready deployment

set -e

echo "🚀 Starting Place Recommendation API..."

# Wait for database services to be ready
echo "⏳ Waiting for database services..."
python scripts/wait_for_db.py

# Run database migrations (safe for production)
echo "📊 Running database migrations..."
alembic upgrade head

# Optionally seed data if in debug mode
if [ "$DEBUG_SEED_DATA" = "true" ]; then
    echo "🌱 Seeding debug data..."
    python scripts/seed_data.py
fi

# Start the application
echo "🚀 Starting FastAPI application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
