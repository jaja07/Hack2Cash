from pydantic import Field, SecretStr
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
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD.get_secret_value()}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # # --- JWT Configuration ---
    # SECRET_KEY: str = Field(..., validation_alias="SECRET_KEY")
    # ALGORITHM: str = "HS256"
    # ACCESS_TOKEN_EXPIRE_MINUTES: float = 60
    

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        extra="ignore",
        env_file_encoding="utf-8"
    )

try:
    settings = Settings() # pyright: ignore
except Exception as e:
    print(f"Warning: Failed to load settings from .env file: {e}")
    print("Ensure your .env file exists in the project root with all required environment variables.")
    raise