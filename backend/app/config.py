from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://postgres:password@localhost:5432/stretch_app"
    cors_origins: list[str] = ["http://localhost:3000"]
    environment: str = "development"


settings = Settings()
