from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # JWT設定
    SECRET_KEY: str = "your-secret-key-here"  # 本番環境では.envから読み込む
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24時間

    class Config:
        env_file = ".env"

settings = Settings() 