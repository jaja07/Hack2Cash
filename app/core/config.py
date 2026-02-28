from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    # --- Database Configuration ---
    DB_HOST: str = "localhost"
    DB_PORT: int = 5433
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: SecretStr

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD.get_secret_value()}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )

    # --- JWT Configuration ---
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: float = 60

    # --- Deploy AI Configuration ---
    AUTH_URL: str = "https://api-auth.dev.deploy.ai/oauth2/token"
    API_URL: str = "https://core-api.dev.deploy.ai"
    CLIENT_ID: str = ""
    CLIENT_SECRET: str = ""
    ORG_ID: str = ""

    # --- Tavily Configuration ---
    TAVILY_API_KEY: str = ""
    NVIDIA_API_KEY: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        env_file_encoding="utf-8",
    )


try:
    settings = Settings()  # pyright: ignore
except Exception as e:
    print(f"Warning: Failed to load settings: {e}")
    raise
