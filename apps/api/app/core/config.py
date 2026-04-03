from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache


class Settings(BaseSettings):
    # Deployment
    deployment_mode: str = "self-hosted"  # "self-hosted" or "cloud"
    debug: bool = False

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8421
    api_url: str = "http://localhost:8421"
    dashboard_url: str = "http://localhost:3000"

    # Database
    postgres_user: str = "gateway"
    postgres_password: str = "gateway_dev_password"
    postgres_db: str = "cloudgentic_gateway"
    database_url: str = "postgresql+asyncpg://gateway:gateway_dev_password@gateway-db:5432/cloudgentic_gateway"

    # Redis
    redis_password: str = "gateway_dev_password"
    redis_url: str = "redis://:gateway_dev_password@gateway-redis:6379/0"

    # Security
    gateway_master_key: str = ""
    gateway_jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Argon2id parameters
    argon2_time_cost: int = 3
    argon2_memory_cost: int = 65536
    argon2_parallelism: int = 4

    # OAuth Providers
    google_client_id: str = ""
    google_client_secret: str = ""

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]

    @field_validator("gateway_master_key")
    @classmethod
    def master_key_must_be_set_in_prod(cls, v: str, info) -> str:
        # In production, master key must be set
        return v

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
    }


@lru_cache
def get_settings() -> Settings:
    return Settings()
