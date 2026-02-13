"""
Модуль безопасности и хеширования паролей
"""
import hashlib
import secrets
import string
from typing import Optional
import bcrypt


class PasswordManager:
    """Менеджер для работы с паролями"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Хеширование пароля
        
        Args:
            password: Исходный пароль
            
        Returns:
            Хешированный пароль
        """
        # Генерируем соль и хешируем пароль
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """
        Проверка пароля
        
        Args:
            password: Введенный пароль
            hashed: Хеш пароля из БД
            
        Returns:
            True если пароль верный
        """
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def generate_password(length: int = 12) -> str:
        """
        Генерация случайного пароля
        
        Args:
            length: Длина пароля
            
        Returns:
            Сгенерированный пароль
        """
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """
        Проверка сложности пароля
        
        Args:
            password: Пароль для проверки
            
        Returns:
            (валидность, сообщение об ошибке)
        """
        if len(password) < 8:
            return False, "Пароль должен содержать минимум 8 символов"
        
        if not any(c.isupper() for c in password):
            return False, "Пароль должен содержать хотя бы одну заглавную букву"
        
        if not any(c.islower() for c in password):
            return False, "Пароль должен содержать хотя бы одну строчную букву"
        
        if not any(c.isdigit() for c in password):
            return False, "Пароль должен содержать хотя бы одну цифру"
        
        return True, "OK"


class Session:
    """Класс для управления сессией пользователя"""
    
    def __init__(self):
        self.user_id: Optional[int] = None
        self.username: Optional[str] = None
        self.role_id: Optional[int] = None
        self.role_name: Optional[str] = None
        self.permissions: dict = {}
        self.login_time: Optional[str] = None
        
    def set_user(self, user_data: dict):
        """Установить данные пользователя"""
        self.user_id = user_data.get('id')
        self.username = user_data.get('username')
        self.role_id = user_data.get('role_id')
        self.role_name = user_data.get('role_name')
        self.permissions = {
            'can_read': user_data.get('can_read', False),
            'can_write': user_data.get('can_write', False),
            'can_delete': user_data.get('can_delete', False),
            'can_approve': user_data.get('can_approve', False),
            'can_admin': user_data.get('can_admin', False)
        }
        from datetime import datetime
        self.login_time = datetime.now()
        
    def clear(self):
        """Очистить сессию"""
        self.user_id = None
        self.username = None
        self.role_id = None
        self.role_name = None
        self.permissions = {}
        self.login_time = None
        
    def has_permission(self, permission: str) -> bool:
        """Проверить наличие права"""
        return self.permissions.get(permission, False)
    
    def is_authenticated(self) -> bool:
        """Проверить аутентификацию"""
        return self.user_id is not None


# Глобальная сессия
current_session = Session()
