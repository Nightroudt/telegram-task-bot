from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str
    database_url: str = "postgresql+asyncpg://taskbot:taskbot@localhost:5432/taskbot"
    log_level: str = "INFO"


settings = Settings()
