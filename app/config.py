from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Pydantic BaseSettings class for environment variables"""
    supabase_url: str
    supabase_key: str
    jwt_secret: str
    jwt_algorithm: str = "HS256"

    supabase_db_url: str | None = None
    supabase_service_key: str | None = None

    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    fcm_server_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = Settings()
