from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QShortcut, QKeySequence

from db.database import init_db
from config import *
from session import current_user, has_permission, logout

from widgets.sidebar import CompactSidebar
from widgets.header_bar import HeaderBar
from widgets.status_bar import StatusBar
from widgets.command_palette import CommandPalette

from views.dashboard_view import DashboardView
from views.grades_view import GradesView
from views.students_view import StudentsView
from views.teachers_view import TeachersView
from views.enrollment_view import EnrollmentView
from views.expenses_view import ExpensesView
from views.subjects_view import SubjectsView
from views.backup_view import BackupView
from views.editor_view import EditorView
from views.settings_view import SettingsView

SIDEBAR_TO_KEY = {
    "inicio": "dashboard",
    "dashboard": "dashboard",
    "notas": "grades",
    "estudiantes": "students",
    "docentes": "teachers",
    "asignaturas": "subjects",
    "matricula": "enrollment",
    "gastos": "expenses",
    "backup": "backup",
    "editor": "editor",
    "configuracion": "settings",
}

VIEW_CLASSES = {
    "dashboard": DashboardView,
    "grades": GradesView,
    "students": StudentsView,
    "teachers": TeachersView,
    "subjects": SubjectsView,
    "enrollment": EnrollmentView,
    "expenses": ExpensesView,
    "editor": EditorView,
    "backup": BackupView,
    "settings": SettingsView,
}

PAGE_LABELS_SINGULAR = {
    "dashboard": "Dashboard",
    "inicio": "Inicio",
    "grades": "Notas",
    "students": "Estudiantes",
    "teachers": "Docentes",
    "subjects": "Asignaturas",
    "enrollment": "Matrícula",
    "gastos": "Gastos",
    "backup": "Backup",
    "editor": "Editor",
    "settings": "Configuración",
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        init_db()
        self.setWindowTitle(f"{APP_NAME}")
        self.setMinimumSize(1200, 750)
        self.resize(1280, 800)

        self._view_widgets = {}
        self._view_keys = []
        self._view_index = {}

        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.header_bar = HeaderBar()
        root.addWidget(self.header_bar)

        mid = QHBoxLayout()
        mid.setContentsMargins(0, 0, 0, 0)
        mid.setSpacing(0)

        self.sidebar = CompactSidebar()
        self.sidebar.page_changed.connect(self._navigate)
        mid.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background: {COLOR_BG};")
        mid.addWidget(self.stack, 1)

        root.addLayout(mid)

        self.status_bar = StatusBar()
        root.addWidget(self.status_bar)

        self._init_views()
        self._setup_shortcuts()
        self._setup_status()

        self._show_first_available()

    def _init_views(self):
        for perm_key, view_class in VIEW_CLASSES.items():
            if has_permission(perm_key):
                view = view_class(self)
                self._view_widgets[perm_key] = view
                self.stack.addWidget(view)
                self._view_index[perm_key] = self.stack.indexOf(view)
                self._view_keys.append(perm_key)

    def _setup_status(self):
        user = current_user()
        if user:
            self.header_bar.set_user(user.get("username", ""))
            self.status_bar.update_user(user.get("username", ""))
            self.status_bar.update_school_year("2025-2026")

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl+F"), self, self._focus_search)
        QShortcut(QKeySequence("Ctrl+K"), self, self._show_command_palette)
        QShortcut(QKeySequence("F5"), self, self._refresh_current)
        QShortcut(QKeySequence("Escape"), self, self._on_escape)

    def _focus_search(self):
        self.header_bar.search_input.setFocus()
        self.header_bar.search_input.selectAll()

    def _refresh_current(self):
        w = self.stack.currentWidget()
        if hasattr(w, "refresh"):
            w.refresh()

    def _on_escape(self):
        w = self.stack.currentWidget()
        if hasattr(w, "on_escape"):
            w.on_escape()

    def _show_first_available(self):
        for key in self._view_keys:
            self._navigate(key)
            return

    def _navigate(self, sidebar_key):
        perm_key = SIDEBAR_TO_KEY.get(sidebar_key, sidebar_key)
        if perm_key not in self._view_widgets:
            return
        self.sidebar.set_active_page(sidebar_key)
        w = self._view_widgets[perm_key]
        self.stack.setCurrentWidget(w)
        label = PAGE_LABELS_SINGULAR.get(sidebar_key, perm_key)
        self.header_bar.set_breadcrumb(f"Inicio / {label}")
        if hasattr(w, "refresh"):
            w.refresh()

    def refresh_stats(self):
        if "dashboard" in self._view_widgets:
            self._view_widgets["dashboard"].refresh()

    def show_student_in_panel(self, student_data):
        sidebar_key = self.sidebar._current_page
        perm_key = SIDEBAR_TO_KEY.get(sidebar_key, sidebar_key)
        if perm_key == "grades" and "grades" in self._view_widgets:
            self._view_widgets["grades"].show_student_panel(student_data)

    def _show_command_palette(self):
        dlg = CommandPalette(self)
        dlg.command_selected.connect(self._on_command)
        dlg.exec()

    def _on_command(self, key):
        if ":" in key:
            action = key.split(":")[1]
            base = key.split(":")[0]
            if action == "export" and base == "grades":
                if "grades" in self._view_widgets:
                    self._view_widgets["grades"]._export_dialog()
                return
            elif action == "new" and base == "students":
                if "students" in self._view_widgets:
                    pass
                return
        if key in self._view_widgets:
            self._navigate(key)
