from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = "darpaa-moe-intermediary-layer"
    database_url: str = Field(default="postgresql://postgres:postgres@localhost:5432/app", alias="DATABASE_URL")
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    secret_key: str = Field(default="dev-secret", alias="SECRET_KEY")
    otel_endpoint: str = Field(default="http://localhost:4317", alias="OTEL_EXPORTER_OTLP_ENDPOINT")
    max_latency_ms: int = 2000
    max_cost_units: int = 1000
    environment: str = "dev"
    hmac_secret: str = Field(default="audit-secret", alias="HMAC_SECRET")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
