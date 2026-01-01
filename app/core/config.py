from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "darpaa-moe-intermediary-layer"
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/app",
        alias="DATABASE_URL",
    )
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    secret_key: str = Field(default="dev-secret", alias="SECRET_KEY")
    otel_endpoint: str = Field(default="http://localhost:4317", alias="OTEL_EXPORTER_OTLP_ENDPOINT")
    max_latency_ms: int = 2000
    max_cost_units: int = 1000
    environment: str = "dev"
    hmac_secret: str = Field(default="audit-secret", alias="HMAC_SECRET")
    llm_enabled: bool = Field(default=False, alias="LLM_ENABLED")
    llm_provider: str = Field(default="openai", alias="LLM_PROVIDER")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.1, alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=512, alias="LLM_MAX_TOKENS")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: str | None = Field(default=None, alias="ANTHROPIC_API_KEY")
    openai_base_url: str = Field(default="https://api.openai.com", alias="OPENAI_BASE_URL")
    anthropic_base_url: str = Field(default="https://api.anthropic.com", alias="ANTHROPIC_BASE_URL")
    tool_max_retries: int = Field(default=2, alias="TOOL_MAX_RETRIES")
    offline_mode: bool = Field(default=True, alias="OFFLINE_MODE")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
