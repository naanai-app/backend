from typing import Any, Dict, List, Optional, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
import secrets


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    PROJECT_NAME: str = "NaaNai API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"
    
    # CORS
    BACKEND_CORS_ORIGINS: str = ""

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "place_recommendation"
    POSTGRES_PORT: str = "5432"
    
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # Neo4j Graph Database
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"
    
    # Google Maps API (optional)
    GOOGLE_MAPS_API_KEY: Optional[str] = None

    # S3 media (optional)
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "ru-central1"
    AWS_S3_BUCKET: Optional[str] = None
    AWS_S3_ENDPOINT_URL: Optional[str] = None
    MEDIA_PRESIGNED_URL_EXPIRE_SECONDS: int = 900

    # Recommendation gRPC service
    RECOMMENDATION_GRPC_HOST: str = "localhost"
    RECOMMENDATION_GRPC_PORT: int = 50051
    RECOMMENDATION_GRPC_TIMEOUT_SECONDS: float = 5.0

    # Interaction event stream (Redis Streams)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_STREAM_ENABLED: bool = True
    REDIS_INTERACTION_STREAM_KEY: str = "stream:user_interactions"
    
    # Debug settings
    DEBUG_SEED_DATA: bool = False
    
    # Email settings (for future notifications)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[str] = None
    EMAILS_FROM_NAME: Optional[str] = None

settings = Settings()
