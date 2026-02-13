"""
Модуль управления подключением к БД SQLite
"""
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Any, List, Dict
import logging
from datetime import datetime
import shutil

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Класс для управления подключением к SQLite БД"""
    
    def __init__(self, db_path: Path, check_same_thread: bool = False):
        """
        Инициализация подключения к БД
        
        Args:
            db_path: Путь к файлу БД
            check_same_thread: Проверка потоков (False для многопоточности)
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Локальное хранилище для подключений в разных потоках
        self._local = threading.local()
        self._check_same_thread = check_same_thread
        
        # Инициализируем БД при первом запуске
        if not self.db_path.exists():
            logger.info(f"Создание новой БД: {self.db_path}")
            self._initialize_database()
        else:
            logger.info(f"Подключение к существующей БД: {self.db_path}")
            
    @property
    def connection(self) -> sqlite3.Connection:
        """Получить подключение для текущего потока"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=self._check_same_thread,
                isolation_level=None  # Автокоммит для простоты
            )
            # Включаем поддержку внешних ключей
            self._local.connection.execute("PRAGMA foreign_keys = ON")
            # Оптимизация для больших объемов данных
            self._local.connection.execute("PRAGMA journal_mode = WAL")
            self._local.connection.execute("PRAGMA synchronous = NORMAL")
            self._local.connection.execute("PRAGMA cache_size = 10000")
            self._local.connection.execute("PRAGMA temp_store = MEMORY")
            
            # Регистрируем адаптеры для datetime
            self._local.connection.row_factory = sqlite3.Row
            
        return self._local.connection
    
    @contextmanager
    def transaction(self):
        """Контекстный менеджер для транзакций"""
        conn = self.connection
        try:
            conn.execute("BEGIN")
            yield conn
            conn.execute("COMMIT")
        except Exception as e:
            conn.execute("ROLLBACK")
            logger.error(f"Ошибка транзакции: {e}")
            raise
            
    def execute(self, query: str, params: Optional[tuple] = None) -> sqlite3.Cursor:
        """
        Выполнить SQL запрос
        
        Args:
            query: SQL запрос
            params: Параметры запроса
            
        Returns:
            Курсор с результатами
        """
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor
        except sqlite3.Error as e:
            logger.error(f"Ошибка выполнения запроса: {e}\nQuery: {query}\nParams: {params}")
            raise
            
    def executemany(self, query: str, params: List[tuple]) -> sqlite3.Cursor:
        """Выполнить множественный SQL запрос"""
        try:
            cursor = self.connection.cursor()
            cursor.executemany(query, params)
            return cursor
        except sqlite3.Error as e:
            logger.error(f"Ошибка выполнения множественного запроса: {e}")
            raise
            
    def fetchone(self, query: str, params: Optional[tuple] = None) -> Optional[sqlite3.Row]:
        """Получить одну запись"""
        cursor = self.execute(query, params)
        return cursor.fetchone()
        
    def fetchall(self, query: str, params: Optional[tuple] = None) -> List[sqlite3.Row]:
        """Получить все записи"""
        cursor = self.execute(query, params)
        return cursor.fetchall()
        
    def backup(self, backup_dir: Path) -> Path:
        """
        Создать резервную копию БД
        
        Args:
            backup_dir: Директория для резервных копий
            
        Returns:
            Путь к созданной резервной копии
        """
        backup_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = backup_dir / f"backup_{timestamp}.db"
        
        try:
            # Используем встроенный механизм backup SQLite
            with sqlite3.connect(str(backup_path)) as backup_conn:
                self.connection.backup(backup_conn)
            
            logger.info(f"Резервная копия создана: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Ошибка создания резервной копии: {e}")
            raise
            
    def restore(self, backup_path: Path):
        """Восстановить БД из резервной копии"""
        if not backup_path.exists():
            raise FileNotFoundError(f"Файл резервной копии не найден: {backup_path}")
            
        try:
            # Закрываем текущее подключение
            if hasattr(self._local, 'connection'):
                self._local.connection.close()
                self._local.connection = None
                
            # Копируем файл резервной копии
            shutil.copy2(backup_path, self.db_path)
            logger.info(f"БД восстановлена из: {backup_path}")
            
        except Exception as e:
            logger.error(f"Ошибка восстановления БД: {e}")
            raise
            
    def _initialize_database(self):
        """Инициализация новой БД"""
        from .migrations import Migration
        migration = Migration(self)
        migration.run_all()
        
    def close(self):
        """Закрыть подключение"""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None
            logger.info("Подключение к БД закрыто")
            
    def __del__(self):
        """Деструктор"""
        self.close()
