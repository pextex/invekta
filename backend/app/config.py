from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / ".env", extra="ignore")
    database_url: str
    crm_allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    crm_cookie_secure: bool = True
    crm_ai_api_key: str = ""
    crm_ai_model: str = "gpt-4.1-mini"

    @property
    def allowed_origins(self) -> set[str]:
        return {
            origin.strip()
            for origin in self.crm_allowed_origins.split(",")
            if origin.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
