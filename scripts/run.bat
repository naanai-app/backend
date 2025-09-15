@echo off
REM Convenience script to run common database operations on Windows

if "%1"=="init" (
    echo 🚀 Initializing database...
    python scripts/init_db.py
    goto :eof
)

if "%1"=="reset" (
    echo ⚠️  Resetting database...
    python scripts/init_db.py --reset
    goto :eof
)

if "%1"=="check" (
    echo 🔍 Checking database health...
    python scripts/check_db.py
    goto :eof
)

if "%1"=="seed" (
    echo 🌱 Seeding data...
    python scripts/seed_data.py
    goto :eof
)

if "%1"=="admin" (
    echo 👤 Creating admin user...
    python scripts/create_admin.py
    goto :eof
)

if "%1"=="dev" (
    echo 🚀 Starting development server...
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    goto :eof
)

echo Usage: %0 {init^|reset^|check^|seed^|admin^|dev}
echo.
echo Commands:
echo   init   - Initialize database tables
echo   reset  - Reset database (WARNING: deletes all data)
echo   check  - Check database connections
echo   seed   - Seed initial data
echo   admin  - Create admin user
echo   dev    - Start development server
