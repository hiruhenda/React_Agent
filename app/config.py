from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Tideline Research Assistant API"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    agent_timeout_seconds: float = 60.0
    max_iterations_default: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()