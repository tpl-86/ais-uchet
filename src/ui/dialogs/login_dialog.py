"""
Диалог входа в систему
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QCheckBox, QMessageBox,
    QGroupBox, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap, QFont
import logging

from ...models.user import User
from ...core.security import current_session

logger = logging.getLogger(__name__)


class LoginDialog(QDialog):
    """Диалог аутентификации пользователя"""
    
    # Сигнал успешного входа
    login_successful = pyqtSignal(dict)
    
    def __init__(self, db_connection=None, parent=None):
        super().__init__(parent)
        self.db = db_connection
        self.current_user = None
        
        self.setWindowTitle("Вход в систему АИС-УЧЕТ")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        # Убираем кнопки минимизации и максимизации
        self.setWindowFlags(
            Qt.WindowType.Dialog | 
            Qt.WindowType.WindowCloseButtonHint
        )
        
        self._setup_ui()
        self._setup_styles()
        
    def _setup_ui(self):
        """Настройка интерфейса"""
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # Заголовок
        title_label = QLabel("АИС учета материальных средств")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Версия
        version_label = QLabel("Версия 2.0.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: gray;")
        layout.addWidget(version_label)
        
        # Разделитель
        layout.addSpacing(20)
        
        # Группа входа
        login_group = QGroupBox("Авторизация")
        login_layout = QVBoxLayout()
        
        # Имя пользователя
        username_layout = QHBoxLayout()
        username_label = QLabel("Пользователь:")
        username_label.setFixedWidth(100)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Введите имя пользователя")
        username_layout.addWidget(username_label)
        username_layout.addWidget(self.username_input)
        login_layout.addLayout(username_layout)
        
        # Пароль
        password_layout = QHBoxLayout()
        password_label = QLabel("Пароль:")
        password_label.setFixedWidth(100)
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        login_layout.addLayout(password_layout)
        
        # Запомнить меня
        self.remember_checkbox = QCheckBox("Запомнить меня")
        login_layout.addWidget(self.remember_checkbox)
        
        login_group.setLayout(login_layout)
        layout.addWidget(login_group)
        
        # Растяжка
        layout.addStretch()
        
        # Кнопки
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.login_button = QPushButton("Войти")
        self.login_button.setDefault(True)
        self.login_button.clicked.connect(self._handle_login)
        
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # Подключение Enter к входу
        self.username_input.returnPressed.connect(self.password_input.setFocus)
        self.password_input.returnPressed.connect(self._handle_login)
        
        # Фокус на поле username
        self.username_input.setFocus()
        
    def _setup_styles(self):
        """Установка стилей"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QLineEdit {
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 12px;
            }
            
            QLineEdit:focus {
                border: 2px solid #4CAF50;
                outline: none;
            }
            
            QPushButton {
                padding: 8px 20px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 12px;
            }
            
            QPushButton#login_button {
                background-color: #4CAF50;
                color: white;
            }
            
            QPushButton#login_button:hover {
                background-color: #45a049;
            }
            
            QPushButton#login_button:pressed {
                background-color: #3d8b40;
            }
            
            QPushButton#cancel_button {
                background-color: #f44336;
                color: white;
            }
            
            QPushButton#cancel_button:hover {
                background-color: #da190b;
            }
        """)
        
        self.login_button.setObjectName("login_button")
        self.cancel_button.setObjectName("cancel_button")
        
    def _handle_login(self):
        """Обработка входа"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username:
            QMessageBox.warning(self, "Ошибка", "Введите имя пользователя")
            self.username_input.setFocus()
            return
        
        if not password:
            QMessageBox.warning(self, "Ошибка", "Введите пароль")
            self.password_input.setFocus()
            return
        
        # Блокируем интерфейс
        self.setEnabled(False)
        
        try:
            # Аутентификация через модель User
            user_model = User(self.db)
            user_data = user_model.authenticate(username, password)
            
            if user_data:
                # Сохраняем данные в сессии
                current_session.set_user(user_data)
                self.current_user = user_data
                
                logger.info(f"Успешный вход пользователя: {username}")
                
                # Сохраняем логин если нужно
                if self.remember_checkbox.isChecked():
                    # TODO: Сохранить в настройках
                    pass
                
                # Отправляем сигнал и закрываем диалог
                self.login_successful.emit(user_data)
                self.accept()
            else:
                QMessageBox.critical(
                    self, 
                    "Ошибка входа", 
                    "Неверное имя пользователя или пароль"
                )
                self.password_input.clear()
                self.password_input.setFocus()
                
        except Exception as e:
            logger.error(f"Ошибка при входе: {e}")
            QMessageBox.critical(
                self, 
                "Ошибка", 
                f"Ошибка подключения к базе данных:\n{str(e)}"
            )
        finally:
            self.setEnabled(True)
    
    def set_database(self, db_connection):
        """Установить подключение к БД"""
        self.db = db_connection
