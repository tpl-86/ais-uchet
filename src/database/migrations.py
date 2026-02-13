"""
Система миграций БД
"""
import logging
from pathlib import Path
from typing import List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class Migration:
    """Класс для управления миграциями БД"""
    
    def __init__(self, db_connection):
        """
        Инициализация миграций
        
        Args:
            db_connection: Объект подключения к БД
        """
        self.db = db_connection
        self._create_migrations_table()
        
    def _create_migrations_table(self):
        """Создать таблицу для отслеживания миграций"""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version INTEGER UNIQUE NOT NULL,
                name TEXT NOT NULL,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
    def get_applied_migrations(self) -> List[int]:
        """Получить список примененных миграций"""
        rows = self.db.fetchall("SELECT version FROM migrations ORDER BY version")
        return [row['version'] for row in rows]
        
    def apply_migration(self, version: int, name: str, sql: str):
        """
        Применить миграцию
        
        Args:
            version: Версия миграции
            name: Название миграции
            sql: SQL код миграции
        """
        try:
            with self.db.transaction():
                # Выполняем SQL миграции
                for statement in sql.split(';'):
                    if statement.strip():
                        self.db.execute(statement)
                        
                # Записываем информацию о миграции
                self.db.execute(
                    "INSERT INTO migrations (version, name) VALUES (?, ?)",
                    (version, name)
                )
                
            logger.info(f"Миграция {version} '{name}' успешно применена")
            
        except Exception as e:
            logger.error(f"Ошибка применения миграции {version}: {e}")
            raise
            
    def run_all(self):
        """Выполнить все неприменённые миграции"""
        applied = self.get_applied_migrations()
        migrations = self._get_all_migrations()
        
        for version, name, sql in migrations:
            if version not in applied:
                logger.info(f"Применение миграции {version}: {name}")
                self.apply_migration(version, name, sql)
                
        logger.info("Все миграции применены")
        
    def _get_all_migrations(self) -> List[Tuple[int, str, str]]:
        """Получить список всех миграций"""
        migrations = [
            (1, "initial_schema", self._get_initial_schema()),
            (2, "add_indexes", self._get_indexes_migration()),
            (3, "initial_data", self._get_initial_data()),
        ]
        return migrations
        
    def _get_initial_schema(self) -> str:
        """Получить SQL для создания начальной схемы"""
        schema_path = Path(__file__).parent / "schema.sql"
        if schema_path.exists():
            with open(schema_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # Базовая схема, если файл не найден
            return self._get_embedded_schema()
            
    def _get_embedded_schema(self) -> str:
        """Встроенная схема БД"""
        return """
        -- Пользователи системы
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            full_name VARCHAR(200) NOT NULL,
            position VARCHAR(200),
            is_active BOOLEAN DEFAULT 1,
            role_id INTEGER NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (role_id) REFERENCES roles(id)
        );

        -- Роли пользователей
        CREATE TABLE roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(50) UNIQUE NOT NULL,
            description TEXT,
            can_read BOOLEAN DEFAULT 1,
            can_write BOOLEAN DEFAULT 0,
            can_delete BOOLEAN DEFAULT 0,
            can_approve BOOLEAN DEFAULT 0,
            can_admin BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Журнал аудита
        CREATE TABLE audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action VARCHAR(50) NOT NULL,
            table_name VARCHAR(50) NOT NULL,
            record_id INTEGER,
            old_values JSON,
            new_values JSON,
            ip_address VARCHAR(50),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        -- Секции/отделы
        CREATE TABLE departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code VARCHAR(2) UNIQUE NOT NULL,
            name VARCHAR(200) NOT NULL,
            parent_id INTEGER,
            head_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (parent_id) REFERENCES departments(id),
            FOREIGN KEY (head_id) REFERENCES officials(id)
        );

        -- Должностные лица
        CREATE TABLE officials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            military_unit VARCHAR(10),
            department_id INTEGER,
            position VARCHAR(200) NOT NULL,
            rank VARCHAR(100),
            full_name VARCHAR(200) NOT NULL,
            is_responsible BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments(id)
        );

        -- Группы материальных средств
        CREATE TABLE material_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code VARCHAR(5) UNIQUE NOT NULL,
            name VARCHAR(200) NOT NULL,
            department_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments(id)
        );

        -- Основной номенклатурный справочник
        CREATE TABLE nomenclature (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code CHAR(10) UNIQUE NOT NULL,
            okp_code VARCHAR(20),
            name VARCHAR(500) NOT NULL,
            unit VARCHAR(50) NOT NULL,
            price DECIMAL(15,2) DEFAULT 0,
            weight_unit DECIMAL(10,3),
            weight_total DECIMAL(10,3),
            
            class_code CHAR(2) GENERATED ALWAYS AS (SUBSTR(code, 1, 2)) STORED,
            group_code CHAR(3) GENERATED ALWAYS AS (SUBSTR(code, 3, 3)) STORED,
            subgroup_code CHAR(2) GENERATED ALWAYS AS (SUBSTR(code, 6, 2)) STORED,
            item_number CHAR(3) GENERATED ALWAYS AS (SUBSTR(code, 8, 3)) STORED,
            
            department_id INTEGER,
            is_active BOOLEAN DEFAULT 1,
            is_temporary BOOLEAN DEFAULT 0,
            
            base_document VARCHAR(200),
            document_date DATE,
            
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER,
            updated_by INTEGER,
            
            FOREIGN KEY (department_id) REFERENCES departments(id),
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (updated_by) REFERENCES users(id)
        );

        -- Категории качественного состояния
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code INTEGER UNIQUE NOT NULL CHECK(code BETWEEN 1 AND 5),
            name VARCHAR(100) NOT NULL,
            description TEXT
        );
        """
        
    def _get_indexes_migration(self) -> str:
        """Миграция для создания индексов"""
        return """
        CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_date ON audit_log(created_at);
        CREATE INDEX IF NOT EXISTS idx_audit_table ON audit_log(table_name, record_id);
        CREATE INDEX IF NOT EXISTS idx_nomenclature_code ON nomenclature(code);
        CREATE INDEX IF NOT EXISTS idx_nomenclature_class ON nomenclature(class_code);
        CREATE INDEX IF NOT EXISTS idx_nomenclature_group ON nomenclature(group_code);
        CREATE INDEX IF NOT EXISTS idx_nomenclature_dept ON nomenclature(department_id);
        CREATE INDEX IF NOT EXISTS idx_nomenclature_active ON nomenclature(is_active);
        """
        
    def _get_initial_data(self) -> str:
        """Начальные данные"""
        return """
        -- Роли по умолчанию
        INSERT OR IGNORE INTO roles (name, description, can_read, can_write, can_delete, can_approve, can_admin) VALUES
        ('Администратор', 'Полный доступ', 1, 1, 1, 1, 1),
        ('Оператор', 'Ввод и редактирование данных', 1, 1, 0, 0, 0),
        ('Руководитель', 'Утверждение документов', 1, 1, 0, 1, 0),
        ('Наблюдатель', 'Только просмотр', 1, 0, 0, 0, 0);

        -- Категории качественного состояния
        INSERT OR IGNORE INTO categories (code, name) VALUES
        (1, 'Первая категория'),
        (2, 'Вторая категория'),
        (3, 'Третья категория'),
        (4, 'Четвертая категория'),
        (5, 'Пятая категория');
        
        -- Администратор по умолчанию (пароль: admin)
        INSERT OR IGNORE INTO users (username, password_hash, full_name, position, role_id) 
        VALUES ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY/YEhyFRRMJiJa', 
                'Администратор системы', 'Администратор', 1);
        """
