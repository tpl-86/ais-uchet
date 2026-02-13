"""
Базовый класс для всех моделей
"""
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class BaseModel:
    """Базовый класс модели с CRUD операциями"""
    
    # Эти атрибуты должны быть переопределены в наследниках
    table_name: str = ""
    primary_key: str = "id"
    
    def __init__(self, db_connection, audit_user_id: Optional[int] = None):
        """
        Инициализация модели
        
        Args:
            db_connection: Объект подключения к БД
            audit_user_id: ID пользователя для аудита
        """
        self.db = db_connection
        self.audit_user_id = audit_user_id
        
        if not self.table_name:
            raise ValueError(f"table_name не определен для {self.__class__.__name__}")
            
    def create(self, data: Dict[str, Any]) -> Optional[int]:
        """
        Создать новую запись
        
        Args:
            data: Словарь с данными для создания
            
        Returns:
            ID созданной записи или None при ошибке
        """
        try:
            # Добавляем временные метки
            if 'created_at' not in data:
                data['created_at'] = datetime.now()
            if 'updated_at' not in data:
                data['updated_at'] = datetime.now()
                
            # Добавляем пользователя
            if self.audit_user_id and 'created_by' not in data:
                data['created_by'] = self.audit_user_id
                
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
            
            cursor = self.db.execute(query, tuple(data.values()))
            record_id = cursor.lastrowid
            
            # Аудит
            self._audit_log('CREATE', record_id, None, data)
            
            logger.debug(f"Создана запись в {self.table_name} с ID={record_id}")
            return record_id
            
        except Exception as e:
            logger.error(f"Ошибка создания записи в {self.table_name}: {e}")
            raise
            
    def read(self, record_id: int) -> Optional[Dict[str, Any]]:
        """
        Прочитать запись по ID
        
        Args:
            record_id: ID записи
            
        Returns:
            Словарь с данными или None
        """
        query = f"SELECT * FROM {self.table_name} WHERE {self.primary_key} = ?"
        row = self.db.fetchone(query, (record_id,))
        
        if row:
            return dict(row)
        return None
        
    def update(self, record_id: int, data: Dict[str, Any]) -> bool:
        """
        Обновить запись
        
        Args:
            record_id: ID записи
            data: Новые данные
            
        Returns:
            True при успехе, False при ошибке
        """
        try:
            # Получаем старые данные для аудита
            old_data = self.read(record_id)
            if not old_data:
                logger.warning(f"Запись {record_id} не найдена в {self.table_name}")
                return False
                
            # Добавляем временную метку и пользователя
            data['updated_at'] = datetime.now()
            if self.audit_user_id and 'updated_by' not in data:
                data['updated_by'] = self.audit_user_id
                
            set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
            query = f"UPDATE {self.table_name} SET {set_clause} WHERE {self.primary_key} = ?"
            values = list(data.values()) + [record_id]
            
            self.db.execute(query, tuple(values))
            
            # Аудит
            self._audit_log('UPDATE', record_id, old_data, data)
            
            logger.debug(f"Обновлена запись {record_id} в {self.table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка обновления записи {record_id} в {self.table_name}: {e}")
            return False
            
    def delete(self, record_id: int) -> bool:
        """
        Удалить запись
        
        Args:
            record_id: ID записи
            
        Returns:
            True при успехе, False при ошибке
        """
        try:
            # Получаем данные для аудита
            old_data = self.read(record_id)
            if not old_data:
                logger.warning(f"Запись {record_id} не найдена в {self.table_name}")
                return False
                
            query = f"DELETE FROM {self.table_name} WHERE {self.primary_key} = ?"
            self.db.execute(query, (record_id,))
            
            # Аудит
            self._audit_log('DELETE', record_id, old_data, None)
            
            logger.debug(f"Удалена запись {record_id} из {self.table_name}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления записи {record_id} из {self.table_name}: {e}")
            return False
            
    def find(self, conditions: Dict[str, Any] = None, 
             order_by: str = None, 
             limit: int = None,
             offset: int = None) -> List[Dict[str, Any]]:
        """
        Поиск записей по условиям
        
        Args:
            conditions: Условия поиска
            order_by: Поле для сортировки
            limit: Ограничение количества
            offset: Смещение
            
        Returns:
            Список записей
        """
        query = f"SELECT * FROM {self.table_name}"
        params = []
        
        if conditions:
            where_clauses = []
            for key, value in conditions.items():
                if value is None:
                    where_clauses.append(f"{key} IS NULL")
                elif isinstance(value, (list, tuple)):
                    placeholders = ','.join(['?' for _ in value])
                    where_clauses.append(f"{key} IN ({placeholders})")
                    params.extend(value)
                else:
                    where_clauses.append(f"{key} = ?")
                    params.append(value)
                    
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
                
        if order_by:
            query += f" ORDER BY {order_by}"
            
        if limit:
            query += f" LIMIT {limit}"
            if offset:
                query += f" OFFSET {offset}"
                
        rows = self.db.fetchall(query, tuple(params))
        return [dict(row) for row in rows]
        
    def count(self, conditions: Dict[str, Any] = None) -> int:
        """
        Подсчет количества записей
        
        Args:
            conditions: Условия подсчета
            
        Returns:
            Количество записей
        """
        query = f"SELECT COUNT(*) as cnt FROM {self.table_name}"
        params = []
        
        if conditions:
            where_clauses = []
            for key, value in conditions.items():
                if value is None:
                    where_clauses.append(f"{key} IS NULL")
                else:
                    where_clauses.append(f"{key} = ?")
                    params.append(value)
                    
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
                
        row = self.db.fetchone(query, tuple(params))
        return row['cnt'] if row else 0
        
    def exists(self, conditions: Dict[str, Any]) -> bool:
        """
        Проверка существования записи
        
        Args:
            conditions: Условия проверки
            
        Returns:
            True если запись существует
        """
        return self.count(conditions) > 0
        
    def _audit_log(self, action: str, record_id: Optional[int],
                   old_values: Optional[Dict], new_values: Optional[Dict]):
        """
        Запись в журнал аудита
        
        Args:
            action: Тип действия
            record_id: ID записи
            old_values: Старые значения
            new_values: Новые значения
        """
        if not self.audit_user_id:
            return
            
        try:
            audit_data = {
                'user_id': self.audit_user_id,
                'action': action,
                'table_name': self.table_name,
                'record_id': record_id,
                'old_values': json.dumps(old_values, default=str) if old_values else None,
                'new_values': json.dumps(new_values, default=str) if new_values else None,
                'created_at': datetime.now()
            }
            
            columns = ', '.join(audit_data.keys())
            placeholders = ', '.join(['?' for _ in audit_data])
            query = f"INSERT INTO audit_log ({columns}) VALUES ({placeholders})"
            
            self.db.execute(query, tuple(audit_data.values()))
            
        except Exception as e:
            logger.error(f"Ошибка записи в журнал аудита: {e}")
