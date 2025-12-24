from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Analytics AI"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    #
    MINDSDB_URL: str

    origins: list[str] = []

    # Database
    database_url: Optional[str] | None = None

    # Security
    secret_key: str = "fallback-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Supabase
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str

    # API Keys
    GEMINI_API_KEY: str

    #
    DEMO_ACCOUNT_EMAIL: str
    DEMO_ACCOUNT_PASSWORD: str

    class Config:
        env_file = ".env"


settings = Settings()
