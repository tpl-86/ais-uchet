"""
Точка входа в приложение АИС учета материальных средств
"""
import sys
import os
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent.parent))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from dotenv import load_dotenv
import logging

from src.core.config import Config
from src.core.logger import setup_logger
from src.database.connection import DatabaseConnection
from src.ui.main_window import MainWindow
from src.ui.dialogs.login_dialog import LoginDialog


def setup_application() -> QApplication:
    """Настройка приложения Qt"""
    app = QApplication(sys.argv)
    
    # Настройки приложения
    app.setApplicationName("АИС-УЧЕТ")
    app.setOrganizationName("Your Organization")
    app.setApplicationDisplayName("АИС учета материальных средств")
    
    # Устанавливаем стиль
    app.setStyle("Fusion")
    
    # Глобальные стили
    app.setStyleSheet("""
        QMainWindow {
            background-color: #f5f5f5;
        }
        QMessageBox {
            background-color: white;
        }
        QToolTip {
            background-color: #ffffc0;
            color: black;
            border: 1px solid black;
            padding: 2px;
        }
    """)
    
    return app


def check_requirements() -> bool:
    """Проверка системных требований"""
    import sqlite3
    
    # Проверка версии Python
    if sys.version_info < (3, 11):
        QMessageBox.critical(
            None, 
            "Ошибка", 
            f"Требуется Python версии 3.11 или выше.\n"
            f"Текущая версия: {sys.version}"
        )
        return False
    
    # Проверка SQLite
    if sqlite3.sqlite_version_info < (3, 35, 0):
        QMessageBox.warning(
            None,
            "Предупреждение",
            f"Рекомендуется SQLite версии 3.35 или выше.\n"
            f"Текущая версия: {sqlite3.sqlite_version}"
        )
    
    return True


def main():
    """Главная функция запуска приложения"""
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Создаем приложение Qt
    app = setup_application()
    
    # Проверяем системные требования
    if not check_requirements():
        sys.exit(1)
    
    # Инициализируем конфигурацию
    config = Config()
    
    # Настраиваем логирование
    logger = setup_logger(config)
    logger.info("="*60)
    logger.info("Запуск приложения АИС-УЧЕТ v%s", config.APP_VERSION)
    logger.info("="*60)
    
    try:
        # Инициализируем подключение к БД
        logger.info(f"Подключение к БД: {config.DB_PATH}")
        db = DatabaseConnection(config.DB_PATH)
        
        # Показываем диалог входа
        login_dialog = LoginDialog(db)
        
        if login_dialog.exec() == LoginDialog.DialogCode.Accepted:
            # Получаем данные пользователя
            user_data = login_dialog.current_user
            
            # Создаем и показываем главное окно
            logger.info(f"Открытие главного окна для пользователя: {user_data['username']}")
            main_window = MainWindow(config, db, user_data)
            main_window.show()
            
            # Запускаем главный цикл приложения
            exit_code = app.exec()
            
            logger.info(f"Приложение завершено с кодом: {exit_code}")
            sys.exit(exit_code)
        else:
            logger.info("Вход отменен пользователем")
            sys.exit(0)
            
    except Exception as e:
        logger.critical(f"Критическая ошибка: {e}", exc_info=True)
        
        QMessageBox.critical(
            None, 
            "Критическая ошибка",
            f"Произошла критическая ошибка:\n{str(e)}\n\n"
            "Приложение будет закрыто."
        )
        
        sys.exit(1)
        

if __name__ == "__main__":
    main()
