#!/usr/bin/env python3
"""
Debug entry point for the FastAPI application.
Run this file directly for debugging: python debug_main.py
"""

import sys
import os
import socket

# Add the current directory to Python path so 'app' module can be found
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def find_free_port(start_port=8001, max_port=8010):
    """Find a free port starting from start_port"""
    for port in range(start_port, max_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None

# Now import and run the FastAPI app
if __name__ == "__main__":
    # Setup local environment first
    
    import uvicorn
    from app.main import app
    
    # Find an available port
    port = find_free_port()
    if port is None:
        print("No free ports found between 8001-8010")
        sys.exit(1)
    
    print(f" Starting FastAPI on http://127.0.0.1:{port}")
    print(f" Swagger UI: http://127.0.0.1:{port}/docs")
    print(f" ReDoc: http://127.0.0.1:{port}/redoc")
    print(f" Using SQLite database for local development")
    
    try:
        # Run with uvicorn for development
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=port,
            reload=True,
            log_level="info"
        )
    except Exception as e:
        print(f" Failed to start server: {e}")
        sys.exit(1)
