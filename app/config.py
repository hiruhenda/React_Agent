from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    gemini_api_key: str = ""
    openai_api_key: str = ""
    chroma_persist_dir: str = ".chroma"
    server_port: int = 8000
    agent_timeout_seconds: int = 60
    max_iterations_default: int = 10


settings = Settings()