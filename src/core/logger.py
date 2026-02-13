"""
Настройка логирования для приложения
"""
import logging
import logging.handlers
from pathlib import Path
from typing import Optional


def setup_logger(config) -> logging.Logger:
    """
    Настройка системы логирования
    
    Args:
        config: Объект конфигурации приложения
        
    Returns:
        Настроенный логгер
    """
    # Создаем корневой логгер
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Удаляем существующие обработчики
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Файловый обработчик с ротацией
    if config.LOG_FILE:
        config.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            config.LOG_FILE,
            maxBytes=config.LOG_MAX_SIZE_MB * 1024 * 1024,
            backupCount=config.LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Специальный обработчик для критических ошибок
    error_file = config.LOG_DIR / 'errors.log'
    error_handler = logging.handlers.RotatingFileHandler(
        error_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
    logger.info("="*60)
    logger.info(f"Система логирования инициализирована")
    logger.info(f"Уровень логирования: {config.LOG_LEVEL}")
    logger.info(f"Лог-файл: {config.LOG_FILE}")
    logger.info("="*60)
    
    return logger


class DatabaseLogger:
    """Логгер для операций с БД"""
    
    def __init__(self, user_id: Optional[int] = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.user_id = user_id
        
    def log_operation(self, operation: str, table: str, record_id: Optional[int] = None, **kwargs):
        """
        Логирование операций с БД
        
        Args:
            operation: Тип операции (CREATE, UPDATE, DELETE, etc.)
            table: Название таблицы
            record_id: ID записи
            **kwargs: Дополнительные параметры
        """
        msg = f"[User: {self.user_id}] {operation} on {table}"
        if record_id:
            msg += f" (ID: {record_id})"
        if kwargs:
            msg += f" | {kwargs}"
            
        self.logger.info(msg)
