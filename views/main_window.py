from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, QLabel,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QShortcut, QKeySequence
import json

from db.database import init_db, get_all_custom_sections, get_custom_section
from config import *
from session import current_user, has_permission, logout
from logs.logger import log as log_msg

from services import ServiceRegistry

from widgets.sidebar import CompactSidebar
from widgets.header_bar import HeaderBar
from widgets.status_bar import StatusBar
from widgets.command_palette import CommandPalette

from views.home_view import HomeView
from views.dashboard_view import DashboardView
from views.grades_view import GradesView
from views.students_view import StudentsView
from views.teachers_view import TeachersView
from views.enrollment_view import EnrollmentView
from views.expenses_view import ExpensesView
from views.subjects_view import SubjectsView
from views.backup_view import BackupView
from views.settings_view import SettingsView
from widgets.custom_section_view import CustomSectionView
from widgets.workbook_renderer import WorkbookRenderView

SECTION_TO_VIEW_KEY = {
    "inicio": "inicio",
    "dashboard": "dashboard",
    "notas": "grades",
    "estudiantes": "students",
    "docentes": "teachers",
    "asignaturas": "subjects",
    "matricula": "enrollment",
    "gastos": "expenses",
    "configuracion": "settings",
}

VIEW_CLASSES = {
    "inicio": HomeView,
    "dashboard": DashboardView,
    "grades": GradesView,
    "students": StudentsView,
    "teachers": TeachersView,
    "subjects": SubjectsView,
    "enrollment": EnrollmentView,
    "expenses": ExpensesView,
    "backup": BackupView,
    "settings": SettingsView,
}

PAGE_LABELS_SINGULAR = {
    "inicio": "Inicio",
    "dashboard": "Dashboard",
    "grades": "Notas",
    "students": "Estudiantes",
    "teachers": "Docentes",
    "subjects": "Asignaturas",
    "enrollment": "Matrícula",
    "gastos": "Gastos",
    "backup": "Backup",
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
        self._view_section_map = {}

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

        self._init_services()
        self._init_views()
        self._init_section_views()
        self._setup_shortcuts()
        self._setup_status()

        self._show_first_available()

    def _init_services(self):
        from services.statistics_service import StatisticsService
        from services.spreadsheet_service import SpreadsheetService
        reg = ServiceRegistry.instance()
        reg.register("statistics", StatisticsService())
        reg.register("spreadsheet", SpreadsheetService())

    def _init_views(self):
        for perm_key, view_class in VIEW_CLASSES.items():
            if has_permission(perm_key):
                view = view_class(self)
                self._view_widgets[perm_key] = view
                self.stack.addWidget(view)
                self._view_index[perm_key] = self.stack.indexOf(view)
                self._view_keys.append(perm_key)

    def _init_section_views(self):
        sections = get_all_custom_sections(visible_only=True)
        for sec in sections:
            sk = sec["section_key"]
            if sk in self._view_widgets:
                continue
            view_key = SECTION_TO_VIEW_KEY.get(sk, sk)
            if view_key in VIEW_CLASSES:
                if view_key not in self._view_widgets and has_permission(view_key):
                    view = VIEW_CLASSES[view_key](self)
                    self._view_widgets[view_key] = view
                    self.stack.addWidget(view)
                    self._view_index[view_key] = self.stack.indexOf(view)
                    self._view_keys.append(view_key)
            else:
                self._register_section_view(sec)

    def _register_section_view(self, sec):
        sk = sec["section_key"]
        if sk in self._view_widgets:
            return
        log_msg(f"REGISTER_VIEW section_key={sk} name={sec.get('name')} doc_id={sec.get('document_id')}")
        view = WorkbookRenderView(sec, None, self)
        view.edit_requested.connect(self._edit_workbook_section)
        view.delete_requested.connect(self._delete_workbook_section)
        self._view_widgets[sk] = view
        self.stack.addWidget(view)
        self._view_index[sk] = self.stack.indexOf(view)
        self._view_keys.append(sk)
        self._view_section_map[sk] = sec.get("id")

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
        for preferred in ("inicio", "dashboard"):
            if preferred in self._view_widgets:
                self._navigate(preferred)
                return
        for key in self._view_keys:
            self._navigate(key)
            return

    def _delete_workbook_section(self, section_key):
        from PySide6.QtWidgets import QMessageBox
        from db.database import delete_custom_section
        sec = get_custom_section(section_key)
        if not sec:
            return
        reply = QMessageBox.question(
            self, "Borrar sección",
            f"¿Borrar permanentemente '{sec.get('name')}'? Todos los datos se eliminarán.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        delete_custom_section(sec["id"])
        if section_key in self._view_widgets:
            w = self._view_widgets.pop(section_key)
            self.stack.removeWidget(w)
            w.deleteLater()
        if section_key in self._view_keys:
            self._view_keys.remove(section_key)
        self.sidebar.refresh()
        self._show_first_available()

    def _edit_workbook_section(self, section_key):
        sec = get_custom_section(section_key)
        if not sec:
            return
        self._editing_section_key = section_key
        from widgets.luckysheet_window import LuckySheetWindow
        from views.editor_view import _write_workbook_data, _Handler
        from spreadsheet.services import DocumentService
        wb_json = sec.get("workbook_json")
        if not wb_json:
            doc_id = sec.get("document_id")
            if doc_id:
                doc_svc = DocumentService()
                wb_json = doc_svc.latest_workbook(doc_id) or "[]"
        _write_workbook_data(wb_json or "[]", sec.get("name", "Sección"), section_id=sec.get("id"))
        import socket
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        from http.server import HTTPServer
        from engine.meta_engine import MetaEngine
        _Handler.engine = MetaEngine()
        _Handler.section_id = sec["id"]
        srv = HTTPServer(("127.0.0.1", port), _Handler)
        import threading
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()
        self._ls_window = LuckySheetWindow(port, self)
        self._ls_window.showMaximized()

    def on_luckysheet_closed(self):
        log_msg("LUCKY_CLOSED refreshing sidebar + views")
        self.sidebar.refresh()
        sections = get_all_custom_sections(visible_only=True)
        for sec in sections:
            sk = sec["section_key"]
            view_key = SECTION_TO_VIEW_KEY.get(sk, sk)
            if view_key not in self._view_widgets:
                self._register_section_view(sec)
        sk = getattr(self, '_editing_section_key', None)
        if sk:
            self._editing_section_key = None
            self._navigate(sk)

    def _navigate(self, section_key):
        view_key = SECTION_TO_VIEW_KEY.get(section_key, section_key)
        if view_key not in self._view_widgets:
            if section_key not in self._view_widgets:
                return
            view_key = section_key
        self.sidebar.set_active_page(section_key)

        w = self._view_widgets[view_key]
        sec = get_custom_section(section_key)
        log_msg(f"NAVIGATE section_key={section_key} view_type={type(w).__name__} doc_id={sec.get('document_id') if sec else None}")
        if isinstance(w, CustomSectionView):
            from widgets.workbook_renderer import WorkbookRenderView
            new_view = WorkbookRenderView(sec, None, self)
            new_view.edit_requested.connect(self._edit_workbook_section)
            new_view.delete_requested.connect(self._delete_workbook_section)
            idx = self._view_index[view_key]
            self.stack.removeWidget(w)
            w.deleteLater()
            self.stack.insertWidget(idx, new_view)
            self._view_widgets[view_key] = new_view
            self._view_index[view_key] = self.stack.indexOf(new_view)
            w = new_view

        self.stack.setCurrentWidget(w)
        label = (sec.get("name") if sec else None) or PAGE_LABELS_SINGULAR.get(view_key, view_key)
        self.header_bar.set_breadcrumb(f"Inicio / {label}")
        if hasattr(w, "refresh"):
            w.refresh()

    def refresh_stats(self):
        if "dashboard" in self._view_widgets:
            self._view_widgets["dashboard"].refresh()

    def show_student_in_panel(self, student_data):
        current = self.sidebar._current_page
        view_key = SECTION_TO_VIEW_KEY.get(current, current)
        if view_key == "grades" and "grades" in self._view_widgets:
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
