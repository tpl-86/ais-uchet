"""
Конфигурация приложения
"""
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Класс конфигурации приложения"""
    
    # Пути к файлам и директориям
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    DB_PATH: Path = DATA_DIR / "database" / "ais_uchet.db"
    BACKUP_DIR: Path = DATA_DIR / "backups"
    LOG_DIR: Path = DATA_DIR / "logs"
    
    # Настройки приложения
    APP_NAME: str = os.getenv("APP_NAME", "AIS-UCHET")
    APP_VERSION: str = os.getenv("APP_VERSION", "2.0.0")
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Настройки безопасности
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default-secret-key")
    PASSWORD_SALT: str = os.getenv("PASSWORD_SALT", "default-salt")
    SESSION_TIMEOUT_MINUTES: int = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
    
    # Настройки логирования
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: Path = LOG_DIR / os.getenv("LOG_FILE", "ais_uchet.log")
    LOG_MAX_SIZE_MB: int = int(os.getenv("LOG_MAX_SIZE_MB", "10"))
    LOG_BACKUP_COUNT: int = int(os.getenv("LOG_BACKUP_COUNT", "5"))
    
    # Настройки UI
    THEME: str = os.getenv("THEME", "light")
    LANGUAGE: str = os.getenv("LANGUAGE", "ru_RU")
    WINDOW_WIDTH: int = int(os.getenv("WINDOW_WIDTH", "1280"))
    WINDOW_HEIGHT: int = int(os.getenv("WINDOW_HEIGHT", "720"))
    
    # Производительность
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "True").lower() == "true"
    CACHE_SIZE_MB: int = int(os.getenv("CACHE_SIZE_MB", "100"))
    MAX_CONCURRENT_USERS: int = int(os.getenv("MAX_CONCURRENT_USERS", "70"))
    
    def __post_init__(self):
        """Создаем необходимые директории"""
        for path in [self.DATA_DIR, self.DB_PATH.parent, self.BACKUP_DIR, self.LOG_DIR]:
            path.mkdir(parents=True, exist_ok=True)
