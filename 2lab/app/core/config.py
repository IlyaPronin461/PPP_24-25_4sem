from pydantic import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Основные настройки приложения
    PROJECT_NAME: str = "Encryption Service"
    DEBUG: bool = False

    # Настройки JWT
    SECRET_KEY: str = "your-secret-key-here"  # Замените на случайную строку
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Настройки базы данных
    SQLALCHEMY_DATABASE_URI: str = "sqlite:///./sql_app.db"

    # Настройки Redis и Celery
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # Дополнительные настройки шифрования
    MAX_ENCRYPTION_TEXT_LENGTH: int = 10_000  # Максимальная длина текста для шифрования

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()