"""
Central configuration. Loads everything from environment variables (.env file),
so no secrets are ever hardcoded in the codebase.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    jwt_secret_key: str
    jwt_expire_minutes: int = 120
    pgcrypto_key: str

    class Config:
        env_file = ".env"


settings = Settings()
