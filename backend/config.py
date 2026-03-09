from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    supabase_url: str
    supabase_key: str
    secret_key: str
    allowed_domain: str = "dxgrow.com"
    app_name: str = "DxTools"
    app_version: str = "1.0"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings():
    return Settings()
