"""
Ribbon интерфейс для главного окна
"""
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QTabWidget,
    QPushButton, QLabel, QFrame, QToolButton,
    QButtonGroup, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QIcon, QFont, QPixmap
from typing import Optional, Dict, List


class RibbonButton(QToolButton):
    """Кнопка для Ribbon панели"""
    
    def __init__(self, text: str, icon: Optional[QIcon] = None, 
                 tooltip: str = "", parent=None):
        super().__init__(parent)
        
        self.setText(text)
        if icon:
            self.setIcon(icon)
            self.setIconSize(QSize(32, 32))
            
        self.setToolTip(tooltip)
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        
        # Стиль кнопки
        self.setStyleSheet("""
            QToolButton {
                min-width: 70px;
                min-height: 70px;
                padding: 5px;
                border: 1px solid transparent;
                border-radius: 3px;
            }
            QToolButton:hover {
                background-color: #e3f2fd;
                border: 1px solid #90caf9;
            }
            QToolButton:pressed {
                background-color: #bbdefb;
            }
        """)


class RibbonGroup(QFrame):
    """Группа элементов в Ribbon"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                border: 1px solid #d0d0d0;
                border-radius: 3px;
                margin: 2px;
                padding: 2px;
            }
        """)
        
        # Основной layout
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Layout для кнопок
        self.button_layout = QHBoxLayout()
        self.button_layout.setSpacing(2)
        layout.addLayout(self.button_layout)
        
        # Подпись группы
        label = QLabel(title)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(label)
        
        self.setLayout(layout)
        
    def add_button(self, button: RibbonButton):
        """Добавить кнопку в группу"""
        self.button_layout.addWidget(button)
        
    def add_separator(self):
        """Добавить разделитель"""
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.VLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        self.button_layout.addWidget(separator)


class RibbonTab(QWidget):
    """Вкладка Ribbon"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.layout.setSpacing(5)
        self.setLayout(self.layout)
        
        self.groups: Dict[str, RibbonGroup] = {}
        
    def add_group(self, name: str, title: str) -> RibbonGroup:
        """Добавить группу на вкладку"""
        group = RibbonGroup(title)
        self.groups[name] = group
        self.layout.addWidget(group)
        return group
        
    def add_stretch(self):
        """Добавить растяжку"""
        self.layout.addStretch()


class RibbonWidget(QTabWidget):
    """Главный Ribbon виджет"""
    
    # Сигналы для действий
    action_triggered = pyqtSignal(str)  # Имя действия
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setMaximumHeight(120)
        self.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #d0d0d0;
                background: #f5f5f5;
            }
            QTabBar::tab {
                padding: 5px 15px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #f5f5f5;
                border: 1px solid #d0d0d0;
                border-bottom: 1px solid #f5f5f5;
            }
        """)
        
        # Создаем вкладки
        self._create_home_tab()
        self._create_documents_tab()
        self._create_directories_tab()
        self._create_reports_tab()
        self._create_service_tab()
        
    def _create_home_tab(self):
        """Создать вкладку 'Главная'"""
        tab = RibbonTab()
        
        # Группа "Файл"
        file_group = tab.add_group("file", "Файл")
        
        new_btn = RibbonButton("Новая БД", None, "Создать новую базу данных")
        new_btn.clicked.connect(lambda: self.action_triggered.emit("new_database"))
        file_group.add_button(new_btn)
        
        open_btn = RibbonButton("Открыть", None, "Открыть базу данных")
        open_btn.clicked.connect(lambda: self.action_triggered.emit("open_database"))
        file_group.add_button(open_btn)
        
        backup_btn = RibbonButton("Резервная\nкопия", None, "Создать резервную копию")
        backup_btn.clicked.connect(lambda: self.action_triggered.emit("backup"))
        file_group.add_button(backup_btn)
        
        # Группа "Вид"
        view_group = tab.add_group("view", "Вид")
        
        refresh_btn = RibbonButton("Обновить", None, "Обновить данные")
        refresh_btn.clicked.connect(lambda: self.action_triggered.emit("refresh"))
        view_group.add_button(refresh_btn)
        
        settings_btn = RibbonButton("Настройки", None, "Настройки приложения")
        settings_btn.clicked.connect(lambda: self.action_triggered.emit("settings"))
        view_group.add_button(settings_btn)
        
        # Группа "Пользователь"
        user_group = tab.add_group("user", "Пользователь")
        
        profile_btn = RibbonButton("Профиль", None, "Профиль пользователя")
        profile_btn.clicked.connect(lambda: self.action_triggered.emit("user_profile"))
        user_group.add_button(profile_btn)
        
        logout_btn = RibbonButton("Выход", None, "Выйти из системы")
        logout_btn.clicked.connect(lambda: self.action_triggered.emit("logout"))
        user_group.add_button(logout_btn)
        
        tab.add_stretch()
        self.addTab(tab, "Главная")
        
    def _create_documents_tab(self):
        """Создать вкладку 'Документы'"""
        tab = RibbonTab()
        
        # Группа "Приходные документы"
        income_group = tab.add_group("income", "Приходные")
        
        act_income_btn = RibbonButton("Акт\nприема", None, "Создать акт приема")
        act_income_btn.clicked.connect(lambda: self.action_triggered.emit("act_income"))
        income_group.add_button(act_income_btn)
        
        # Группа "Расходные документы"
        expense_group = tab.add_group("expense", "Расходные")
        
        order_btn = RibbonButton("Наряд", None, "Создать наряд")
        order_btn.clicked.connect(lambda: self.action_triggered.emit("order"))
        expense_group.add_button(order_btn)
        
        distribution_btn = RibbonButton("Разнарядка", None, "Создать разнарядку")
        distribution_btn.clicked.connect(lambda: self.action_triggered.emit("distribution"))
        expense_group.add_button(distribution_btn)
        
        # Группа "Внутренние документы"
        internal_group = tab.add_group("internal", "Внутренние")
        
        act_change_btn = RibbonButton("Акт изм.\nсостояния", None, 
                                      "Акт изменения качественного состояния")
        act_change_btn.clicked.connect(lambda: self.action_triggered.emit("act_change"))
        internal_group.add_button(act_change_btn)
        
        act_writeoff_btn = RibbonButton("Акт\nсписания", None, "Создать акт списания")
        act_writeoff_btn.clicked.connect(lambda: self.action_triggered.emit("act_writeoff"))
        internal_group.add_button(act_writeoff_btn)
        
        # Группа "Журналы"
        journals_group = tab.add_group("journals", "Журналы")
        
        income_book_btn = RibbonButton("Книга\nприхода", None, "Книга приходных документов")
        income_book_btn.clicked.connect(lambda: self.action_triggered.emit("income_book"))
        journals_group.add_button(income_book_btn)
        
        expense_book_btn = RibbonButton("Книга\nрасхода", None, "Книга расходных документов")
        expense_book_btn.clicked.connect(lambda: self.action_triggered.emit("expense_book"))
        journals_group.add_button(expense_book_btn)
        
        tab.add_stretch()
        self.addTab(tab, "Документы")
        
    def _create_directories_tab(self):
        """Создать вкладку 'Справочники'"""
        tab = RibbonTab()
        
        # Группа "Основные"
        main_group = tab.add_group("main", "Основные")
        
        nomenclature_btn = RibbonButton("Номенклатура", None, "Справочник номенклатуры")
        nomenclature_btn.clicked.connect(lambda: self.action_triggered.emit("nomenclature"))
        main_group.add_button(nomenclature_btn)
        
        departments_btn = RibbonButton("Отделы", None, "Справочник отделов")
        departments_btn.clicked.connect(lambda: self.action_triggered.emit("departments"))
        main_group.add_button(departments_btn)
        
        organizations_btn = RibbonButton("Организации", None, "Справочник организаций")
        organizations_btn.clicked.connect(lambda: self.action_triggered.emit("organizations"))
        main_group.add_button(organizations_btn)
        
        # Группа "Дополнительные"
        additional_group = tab.add_group("additional", "Дополнительные")
        
        officials_btn = RibbonButton("Должностные\nлица", None, "Справочник должностных лиц")
        officials_btn.clicked.connect(lambda: self.action_triggered.emit("officials"))
        additional_group.add_button(officials_btn)
        
        metals_btn = RibbonButton("Драг.\nметаллы", None, "Справочник драгметаллов")
        metals_btn.clicked.connect(lambda: self.action_triggered.emit("metals"))
        additional_group.add_button(metals_btn)
        
        tab.add_stretch()
        self.addTab(tab, "Справочники")
        
    def _create_reports_tab(self):
        """Создать вкладку 'Отчеты'"""
        tab = RibbonTab()
        
        # Группа "Основные отчеты"
        main_reports = tab.add_group("main_reports", "Основные")
        
        balance_btn = RibbonButton("Остатки", None, "Отчет по остаткам")
        balance_btn.clicked.connect(lambda: self.action_triggered.emit("report_balance"))
        main_reports.add_button(balance_btn)
        
        turnover_btn = RibbonButton("Оборотная\nведомость", None, "Оборотная ведомость")
        turnover_btn.clicked.connect(lambda: self.action_triggered.emit("report_turnover"))
        main_reports.add_button(turnover_btn)
        
        card_btn = RibbonButton("Учетная\nкарточка", None, "Учетная карточка")
        card_btn.clicked.connect(lambda: self.action_triggered.emit("report_card"))
        main_reports.add_button(card_btn)
        
        # Группа "Инвентаризация"
        inventory_group = tab.add_group("inventory", "Инвентаризация")
        
        inventory_btn = RibbonButton("Ведомость", None, "Ведомость инвентаризации")
        inventory_btn.clicked.connect(lambda: self.action_triggered.emit("report_inventory"))
        inventory_group.add_button(inventory_btn)
        
        # Группа "Экспорт"
        export_group = tab.add_group("export", "Экспорт")
        
        excel_btn = RibbonButton("Excel", None, "Экспорт в Excel")
        excel_btn.clicked.connect(lambda: self.action_triggered.emit("export_excel"))
        export_group.add_button(excel_btn)
        
        pdf_btn = RibbonButton("PDF", None, "Экспорт в PDF")
        pdf_btn.clicked.connect(lambda: self.action_triggered.emit("export_pdf"))
        export_group.add_button(pdf_btn)
        
        tab.add_stretch()
        self.addTab(tab, "Отчеты")
        
    def _create_service_tab(self):
        """Создать вкладку 'Сервис'"""
        tab = RibbonTab()
        
        # Группа "Администрирование"
        admin_group = tab.add_group("admin", "Администрирование")
        
        users_btn = RibbonButton("Пользователи", None, "Управление пользователями")
        users_btn.clicked.connect(lambda: self.action_triggered.emit("users"))
        admin_group.add_button(users_btn)
        
        roles_btn = RibbonButton("Роли", None, "Управление ролями")
        roles_btn.clicked.connect(lambda: self.action_triggered.emit("roles"))
        admin_group.add_button(roles_btn)
        
        audit_btn = RibbonButton("Аудит", None, "Журнал аудита")
        audit_btn.clicked.connect(lambda: self.action_triggered.emit("audit"))
        admin_group.add_button(audit_btn)
        
        # Группа "Импорт/Экспорт"
        import_export = tab.add_group("import_export", "Импорт/Экспорт")
        
        import_btn = RibbonButton("Импорт\nиз DBF", None, "Импорт из старой системы")
        import_btn.clicked.connect(lambda: self.action_triggered.emit("import_dbf"))
        import_export.add_button(import_btn)
        
        # Группа "Обслуживание"
        maintenance_group = tab.add_group("maintenance", "Обслуживание")
        
        check_db_btn = RibbonButton("Проверка\nБД", None, "Проверка целостности БД")
        check_db_btn.clicked.connect(lambda: self.action_triggered.emit("check_db"))
        maintenance_group.add_button(check_db_btn)
        
        optimize_btn = RibbonButton("Оптимизация", None, "Оптимизация БД")
        optimize_btn.clicked.connect(lambda: self.action_triggered.emit("optimize_db"))
        maintenance_group.add_button(optimize_btn)
        
        tab.add_stretch()
        self.addTab(tab, "Сервис")
