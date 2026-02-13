"""
Главное окно приложения
"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStatusBar, QLabel, QMessageBox, QMdiArea,
    QMdiSubWindow, QSplitter, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QDateTime
from PyQt6.QtGui import QAction, QCloseEvent
import logging

from .widgets.ribbon_widget import RibbonWidget
from .dialogs.login_dialog import LoginDialog
from ..core.security import current_session
from ..database.connection import DatabaseConnection

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self, config, db_connection: DatabaseConnection, user_data: dict):
        super().__init__()
        
        self.config = config
        self.db = db_connection
        self.user_data = user_data
        
        # Словарь открытых окон
        self.open_windows = {}
        
        self.setWindowTitle(f"АИС-УЧЕТ - {user_data['full_name']} ({user_data['role_name']})")
        self.setGeometry(100, 100, config.WINDOW_WIDTH, config.WINDOW_HEIGHT)
        
        self._setup_ui()
        self._setup_status_bar()
        self._setup_timers()
        self._check_permissions()
        
        logger.info(f"Главное окно открыто для пользователя: {user_data['username']}")
        
    def _setup_ui(self):
        """Настройка интерфейса"""
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Главный layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Ribbon меню
        self.ribbon = RibbonWidget()
        self.ribbon.action_triggered.connect(self._handle_ribbon_action)
        main_layout.addWidget(self.ribbon)
        
        # Рабочая область с деревом навигации
        work_area = QSplitter(Qt.Orientation.Horizontal)
        
        # Дерево навигации
        self.nav_tree = self._create_navigation_tree()
        work_area.addWidget(self.nav_tree)
        
        # MDI область для документов
        self.mdi_area = QMdiArea()
        self.mdi_area.setViewMode(QMdiArea.ViewMode.TabbedView)
        self.mdi_area.setTabsClosable(True)
        self.mdi_area.setTabsMovable(True)
        work_area.addWidget(self.mdi_area)
        
        # Устанавливаем пропорции
        work_area.setSizes([250, self.config.WINDOW_WIDTH - 250])
        
        main_layout.addWidget(work_area)
        central_widget.setLayout(main_layout)
        
    def _create_navigation_tree(self) -> QTreeWidget:
        """Создать дерево навигации"""
        tree = QTreeWidget()
        tree.setHeaderLabel("Навигация")
        tree.setMinimumWidth(200)
        
        # Стиль дерева
        tree.setStyleSheet("""
            QTreeWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 5px;
                font-size: 12px;
            }
            QTreeWidget::item {
                padding: 5px;
                border-radius: 3px;
            }
            QTreeWidget::item:hover {
                background-color: #e9ecef;
            }
            QTreeWidget::item:selected {
                background-color: #007bff;
                color: white;
            }
        """)
        
        # Документы
        docs_item = QTreeWidgetItem(tree, ["📄 Документы"])
        QTreeWidgetItem(docs_item, ["Приходные документы"])
        QTreeWidgetItem(docs_item, ["Расходные документы"])
        QTreeWidgetItem(docs_item, ["Внутренние документы"])
        docs_item.setExpanded(True)
        
        # Справочники
        dirs_item = QTreeWidgetItem(tree, ["📚 Справочники"])
        QTreeWidgetItem(dirs_item, ["Номенклатура"])
        QTreeWidgetItem(dirs_item, ["Организации"])
        QTreeWidgetItem(dirs_item, ["Отделы"])
        QTreeWidgetItem(dirs_item, ["Должностные лица"])
        dirs_item.setExpanded(True)
        
        # Учет
        account_item = QTreeWidgetItem(tree, ["📊 Учет"])
        QTreeWidgetItem(account_item, ["Остатки МС"])
        QTreeWidgetItem(account_item, ["Учетные карточки"])
        QTreeWidgetItem(account_item, ["Движение МС"])
        account_item.setExpanded(True)
        
        # Отчеты
        reports_item = QTreeWidgetItem(tree, ["📈 Отчеты"])
        QTreeWidgetItem(reports_item, ["Оборотная ведомость"])
        QTreeWidgetItem(reports_item, ["Сводка наличия"])
        QTreeWidgetItem(reports_item, ["Инвентаризация"])
        
        # Сервис
        if current_session.has_permission('can_admin'):
            service_item = QTreeWidgetItem(tree, ["⚙️ Сервис"])
            QTreeWidgetItem(service_item, ["Пользователи"])
            QTreeWidgetItem(service_item, ["Резервное копирование"])
            QTreeWidgetItem(service_item, ["Импорт данных"])
            QTreeWidgetItem(service_item, ["Журнал аудита"])
        
        # Обработка клика
        tree.itemClicked.connect(self._handle_tree_click)
        
        return tree
    
    def _handle_tree_click(self, item: QTreeWidgetItem, column: int):
        """Обработка клика по дереву навигации"""
        item_text = item.text(0)
        
        # Словарь соответствия элементов дерева и действий
        actions_map = {
            "Номенклатура": "nomenclature",
            "Организации": "organizations",
            "Отделы": "departments",
            "Остатки МС": "stock_balance",
            "Учетные карточки": "accounting_cards",
            "Приходные документы": "income_documents",
            "Расходные документы": "expense_documents",
            "Пользователи": "users",
            "Журнал аудита": "audit_log",
            "Оборотная ведомость": "report_turnover",
            "Сводка наличия": "report_balance"
        }
        
        action = actions_map.get(item_text)
        if action:
            self._handle_ribbon_action(action)
    
    def _setup_status_bar(self):
        """Настройка статусной строки"""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        
        # Пользователь
        self.user_label = QLabel(f"👤 {self.user_data['full_name']}")
        status_bar.addWidget(self.user_label)
        
        # Роль
        self.role_label = QLabel(f"🔑 {self.user_data['role_name']}")
        status_bar.addWidget(self.role_label)
        
        # Разделитель
        status_bar.addWidget(QLabel(" | "))
        
        # База данных
        db_name = self.db.db_path.name
        self.db_label = QLabel(f"💾 {db_name}")
        status_bar.addWidget(self.db_label)
        
        # Растяжка
        status_bar.addPermanentWidget(QLabel(""))
        
        # Время
        self.time_label = QLabel()
        status_bar.addPermanentWidget(self.time_label)
        
    def _setup_timers(self):
        """Настройка таймеров"""
        # Таймер для обновления времени
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self._update_time)
        self.time_timer.start(1000)  # Каждую секунду
        
        # Таймер для автоматического резервного копирования
        if self.config.DEBUG:
            # В режиме отладки - каждые 5 минут
            backup_interval = 5 * 60 * 1000
        else:
            # В рабочем режиме - каждый час
            backup_interval = 60 * 60 * 1000
            
        self.backup_timer = QTimer()
        self.backup_timer.timeout.connect(self._auto_backup)
        self.backup_timer.start(backup_interval)
        
    def _update_time(self):
        """Обновить время в статусной строке"""
        current_time = QDateTime.currentDateTime().toString("dd.MM.yyyy hh:mm:ss")
        self.time_label.setText(f"🕐 {current_time}")
        
    def _auto_backup(self):
        """Автоматическое резервное копирование"""
        try:
            backup_path = self.db.backup(self.config.BACKUP_DIR)
            logger.info(f"Автоматическое резервное копирование: {backup_path}")
            self.statusBar().showMessage("✅ Резервная копия создана", 5000)
        except Exception as e:
            logger.error(f"Ошибка автоматического резервного копирования: {e}")
            
    def _check_permissions(self):
        """Проверка и установка прав доступа"""
        # Отключаем элементы интерфейса в зависимости от прав
        if not current_session.has_permission('can_write'):
            # Отключаем создание и редактирование
            pass
            
        if not current_session.has_permission('can_delete'):
            # Отключаем удаление
            pass
            
        if not current_session.has_permission('can_admin'):
            # Скрываем вкладку "Сервис"
            self.ribbon.setTabEnabled(4, False)  # Вкладка "Сервис"
            
    def _handle_ribbon_action(self, action: str):
        """Обработка действий из Ribbon меню"""
        logger.debug(f"Ribbon action: {action}")
        
        # Проверяем права
        if action in ['users', 'roles', 'audit'] and not current_session.has_permission('can_admin'):
            QMessageBox.warning(self, "Доступ запрещен", 
                               "У вас недостаточно прав для выполнения этого действия")
            return
            
        # Словарь обработчиков действий
        handlers = {
            # Файл
            'new_database': self._new_database,
            'open_database': self._open_database,
            'backup': self._create_backup,
            'logout': self._logout,
            
            # Документы
            'act_income': self._open_act_income,
            'order': self._open_order,
            'income_book': self._open_income_book,
            'expense_book': self._open_expense_book,
            
            # Справочники
            'nomenclature': self._open_nomenclature,
            'departments': self._open_departments,
            'organizations': self._open_organizations,
            'officials': self._open_officials,
            
            # Отчеты
            'report_balance': self._open_report_balance,
            'report_turnover': self._open_report_turnover,
            'report_card': self._open_report_card,
            
            # Сервис
            'users': self._open_users_management,
            'audit': self._open_audit_log,
            'import_dbf': self._import_from_dbf,
            
            # Прочее
            'settings': self._open_settings,
            'refresh': self._refresh_current_window,
        }
        
        handler = handlers.get(action)
        if handler:
            try:
                handler()
            except Exception as e:
                logger.error(f"Ошибка выполнения действия {action}: {e}")
                QMessageBox.critical(self, "Ошибка", 
                                    f"Ошибка выполнения операции:\n{str(e)}")
        else:
            # Временная заглушка для нереализованных функций
            QMessageBox.information(self, "В разработке", 
                                  f"Функция '{action}' находится в разработке")
            
    def _open_window(self, window_class, title: str, *args, **kwargs):
        """Универсальный метод открытия окна в MDI области"""
        # Проверяем, не открыто ли уже окно
        if title in self.open_windows:
            # Активируем существующее окно
            self.mdi_area.setActiveSubWindow(self.open_windows[title])
            return self.open_windows[title].widget()
            
        try:
            # Создаем новое окно
            widget = window_class(self.db, *args, **kwargs)
            sub_window = self.mdi_area.addSubWindow(widget)
            sub_window.setWindowTitle(title)
            sub_window.show()
            
            # Сохраняем ссылку
            self.open_windows[title] = sub_window
            
            # Удаляем из словаря при закрытии
            sub_window.destroyed.connect(lambda: self.open_windows.pop(title, None))
            
            return widget
            
        except Exception as e:
            logger.error(f"Ошибка открытия окна {title}: {e}")
            raise
            
    # Заглушки для обработчиков (будут реализованы далее)
    def _new_database(self):
        """Создать новую БД"""
        QMessageBox.information(self, "Новая БД", "Функция создания новой БД")
        
    def _open_database(self):
        """Открыть БД"""
        QMessageBox.information(self, "Открыть БД", "Функция открытия БД")
        
    def _create_backup(self):
        """Создать резервную копию"""
        try:
            backup_path = self.db.backup(self.config.BACKUP_DIR)
            QMessageBox.information(self, "Резервная копия", 
                                  f"Резервная копия создана:\n{backup_path}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка создания резервной копии:\n{str(e)}")
            
    def _logout(self):
        """Выход из системы"""
        reply = QMessageBox.question(self, "Выход", 
                                    "Вы действительно хотите выйти из системы?",
                                    QMessageBox.StandardButton.Yes | 
                                    QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            current_session.clear()
            self.close()
            
            # Показываем диалог входа снова
            login_dialog = LoginDialog(self.db)
            if login_dialog.exec() == LoginDialog.DialogCode.Accepted:
                # Создаем новое главное окно
                new_window = MainWindow(self.config, self.db, login_dialog.current_user)
                new_window.show()
                
    def _refresh_current_window(self):
        """Обновить текущее окно"""
        active_window = self.mdi_area.activeSubWindow()
        if active_window and hasattr(active_window.widget(), 'refresh'):
            active_window.widget().refresh()
            
    # Методы-заглушки для открытия окон (будут реализованы в следующих шагах)
    def _open_act_income(self): pass
    def _open_order(self): pass
    def _open_income_book(self): pass
    def _open_expense_book(self): pass
    def _open_nomenclature(self): pass
    def _open_departments(self): pass
    def _open_organizations(self): pass
    def _open_officials(self): pass
    def _open_report_balance(self): pass
    def _open_report_turnover(self): pass
    def _open_report_card(self): pass
    def _open_users_management(self): pass
    def _open_audit_log(self): pass
    def _open_settings(self): pass
    def _import_from_dbf(self): pass
    
    def closeEvent(self, event: QCloseEvent):
        """Обработка закрытия окна"""
        reply = QMessageBox.question(
            self, 
            "Закрытие программы",
            "Вы действительно хотите закрыть программу?\n"
            "Все несохраненные данные будут потеряны.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Закрываем все подокна
            self.mdi_area.closeAllSubWindows()
            
            # Останавливаем таймеры
            self.time_timer.stop()
            self.backup_timer.stop()
            
            # Очищаем сессию
            current_session.clear()
            
            # Закрываем подключение к БД
            self.db.close()
            
            logger.info(f"Приложение закрыто пользователем: {self.user_data['username']}")
            event.accept()
        else:
            event.ignore()
