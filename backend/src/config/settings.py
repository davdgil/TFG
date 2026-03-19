from pydantic_settings import BaseSettings
from pathlib import Path

# Path absoluto al .env (está en backend/)
ENV_PATH = Path(__file__).resolve().parent.parent.parent / ".env"

class Settings(BaseSettings):
    db_uri: str
    db_name: str
    port: int = 9000
    jwt_secret: str

    class Config:
        env_file = ENV_PATH
        env_file_encoding = "utf-8"


settings = Settings()
