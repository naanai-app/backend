from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.core.graph_db import graph_db
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await graph_db.connect()
    yield
    # Shutdown
    await graph_db.close()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="NaaNai API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set all CORS enabled origins
cors_origins = []
if settings.BACKEND_CORS_ORIGINS:
    if settings.BACKEND_CORS_ORIGINS.startswith("[") and settings.BACKEND_CORS_ORIGINS.endswith("]"):
        # Handle JSON-like string format
        import json
        try:
            cors_origins = json.loads(settings.BACKEND_CORS_ORIGINS)
        except json.JSONDecodeError:
            # If JSON parsing fails, treat as comma-separated
            cors_origins = [i.strip() for i in settings.BACKEND_CORS_ORIGINS.strip("[]").replace('"', '').split(",") if i.strip()]
    else:
        # Handle comma-separated string
        cors_origins = [i.strip() for i in settings.BACKEND_CORS_ORIGINS.split(",") if i.strip()]

if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {"message": "NaaNai API", "version": settings.VERSION}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
