"""
Модель пользователя и ролей
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from .base import BaseModel
from ..core.security import PasswordManager

logger = logging.getLogger(__name__)


class Role(BaseModel):
    """Модель ролей пользователей"""
    
    table_name = "roles"
    
    def get_permissions(self, role_id: int) -> Dict[str, bool]:
        """
        Получить права роли
        
        Args:
            role_id: ID роли
            
        Returns:
            Словарь с правами
        """
        role = self.read(role_id)
        if role:
            return {
                'can_read': role.get('can_read', False),
                'can_write': role.get('can_write', False),
                'can_delete': role.get('can_delete', False),
                'can_approve': role.get('can_approve', False),
                'can_admin': role.get('can_admin', False)
            }
        return {}
    
    def get_all_roles(self) -> List[Dict[str, Any]]:
        """Получить все роли"""
        return self.find(order_by="name")


class User(BaseModel):
    """Модель пользователя"""
    
    table_name = "users"
    
    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Аутентификация пользователя
        
        Args:
            username: Имя пользователя
            password: Пароль
            
        Returns:
            Данные пользователя или None
        """
        # Получаем пользователя по имени
        query = """
            SELECT u.*, r.name as role_name, 
                   r.can_read, r.can_write, r.can_delete, 
                   r.can_approve, r.can_admin
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.username = ? AND u.is_active = 1
        """
        
        row = self.db.fetchone(query, (username,))
        if not row:
            logger.warning(f"Попытка входа с несуществующим пользователем: {username}")
            return None
        
        user_data = dict(row)
        
        # Проверяем пароль
        if not PasswordManager.verify_password(password, user_data['password_hash']):
            logger.warning(f"Неверный пароль для пользователя: {username}")
            return None
        
        logger.info(f"Успешная аутентификация пользователя: {username}")
        return user_data
    
    def create_user(self, username: str, password: str, full_name: str,
                    position: str, role_id: int) -> Optional[int]:
        """
        Создать нового пользователя
        
        Args:
            username: Имя пользователя
            password: Пароль
            full_name: Полное имя
            position: Должность
            role_id: ID роли
            
        Returns:
            ID созданного пользователя
        """
        # Проверяем уникальность имени пользователя
        if self.exists({'username': username}):
            logger.error(f"Пользователь {username} уже существует")
            return None
        
        # Хешируем пароль
        password_hash = PasswordManager.hash_password(password)
        
        # Создаем пользователя
        user_data = {
            'username': username,
            'password_hash': password_hash,
            'full_name': full_name,
            'position': position,
            'role_id': role_id,
            'is_active': 1
        }
        
        user_id = self.create(user_data)
        if user_id:
            logger.info(f"Создан пользователь: {username} (ID: {user_id})")
        
        return user_id
    
    def change_password(self, user_id: int, old_password: str, 
                       new_password: str) -> bool:
        """
        Изменить пароль пользователя
        
        Args:
            user_id: ID пользователя
            old_password: Старый пароль
            new_password: Новый пароль
            
        Returns:
            True при успехе
        """
        user = self.read(user_id)
        if not user:
            return False
        
        # Проверяем старый пароль
        if not PasswordManager.verify_password(old_password, user['password_hash']):
            logger.warning(f"Неверный старый пароль при смене для пользователя ID: {user_id}")
            return False
        
        # Проверяем сложность нового пароля
        valid, message = PasswordManager.validate_password_strength(new_password)
        if not valid:
            logger.warning(f"Слабый новый пароль: {message}")
            return False
        
        # Обновляем пароль
        new_hash = PasswordManager.hash_password(new_password)
        success = self.update(user_id, {'password_hash': new_hash})
        
        if success:
            logger.info(f"Пароль изменен для пользователя ID: {user_id}")
        
        return success
    
    def reset_password(self, user_id: int) -> Optional[str]:
        """
        Сбросить пароль пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Новый временный пароль
        """
        # Генерируем временный пароль
        temp_password = PasswordManager.generate_password()
        password_hash = PasswordManager.hash_password(temp_password)
        
        # Обновляем пароль
        if self.update(user_id, {'password_hash': password_hash}):
            logger.info(f"Пароль сброшен для пользователя ID: {user_id}")
            return temp_password
        
        return None
    
    def get_active_users(self) -> List[Dict[str, Any]]:
        """Получить активных пользователей"""
        query = """
            SELECT u.*, r.name as role_name
            FROM users u
            JOIN roles r ON u.role_id = r.id
            WHERE u.is_active = 1
            ORDER BY u.username
        """
        rows = self.db.fetchall(query)
        return [dict(row) for row in rows]
    
    def deactivate_user(self, user_id: int) -> bool:
        """Деактивировать пользователя"""
        return self.update(user_id, {'is_active': 0})
    
    def activate_user(self, user_id: int) -> bool:
        """Активировать пользователя"""
        return self.update(user_id, {'is_active': 1})
