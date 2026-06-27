from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QStackedWidget, QLabel, QFrame,
)
from PySide6.QtCore import Qt

from db.database import init_db
from config import *
from session import current_user, has_permission, logout

from views.dashboard_view import DashboardView
from views.grades_view import GradesView
from views.students_view import StudentsView
from views.teachers_view import TeachersView
from views.enrollment_view import EnrollmentView
from views.subjects_view import SubjectsView
from views.backup_view import BackupView
from views.editor_view import EditorView
from views.settings_view import SettingsView

NAV_SECTIONS = [
    ("PRINCIPAL", [
        ("dashboard", "Inicio", "\u25c7"),
    ]),
    ("GESTION ACADEMICA", [
        ("grades", "Notas", "\u25a1"),
        ("students", "Estudiantes", "\u25cb"),
        ("teachers", "Profesores", "\u25c7"),
        ("subjects", "Asignaturas", "\u25b3"),
        ("enrollment", "Matricula", "\u00a7"),
    ]),
    ("HERRAMIENTAS", [
        ("editor", "Editor", "\u270e"),
        ("backup", "Backup", "\u21bb"),
    ]),
    ("ADMINISTRACION", [
        ("settings", "Configuracion", "\u2699"),
    ]),
]

VIEW_CLASSES = {
    "dashboard": DashboardView,
    "grades": GradesView,
    "students": StudentsView,
    "teachers": TeachersView,
    "subjects": SubjectsView,
    "enrollment": EnrollmentView,
    "editor": EditorView,
    "backup": BackupView,
    "settings": SettingsView,
}


class NavButton(QPushButton):
    def __init__(self, text, icon_char):
        super().__init__(f"  {icon_char}  {text}")
        self.setCheckable(True)
        self.setFixedHeight(38)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style(False)

    def _update_style(self, checked):
        if checked:
            self.setStyleSheet(f"""
                QPushButton {{
                    text-align: left; padding: 0 16px 0 12px;
                    border: none;
                    font-size: 13px; font-weight: 500;
                    color: #ffffff;
                    background: {COLOR_SIDEBAR_ACTIVE};
                    border-left: 3px solid {COLOR_ACCENT};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    text-align: left; padding: 0 16px 0 15px;
                    border: none;
                    font-size: 13px; font-weight: 400;
                    color: {COLOR_TEXT_MUTED};
                    background: transparent;
                }}
                QPushButton:hover {{
                    background: {COLOR_SIDEBAR_HOVER};
                    color: {COLOR_TEXT};
                }}
            """)

    def set_active(self, active):
        self.setChecked(active)
        self._update_style(active)


class SidebarSection(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet(f"""
            font-size: 10px; color: {COLOR_TEXT_DIM};
            padding: 20px 16px 4px 16px;
            font-weight: 500;
            letter-spacing: 1.5px;
            text-transform: uppercase;
        """)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        init_db()
        self.setWindowTitle(f"{APP_NAME}")
        self.setMinimumSize(1200, 750)
        self.resize(1280, 800)

        self.nav_btns = []
        self.nav_keys = []
        self.view_widgets = []

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = self._build_sidebar()
        layout.addWidget(sidebar)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background: {COLOR_BG};")
        layout.addWidget(self.stack, 1)

        self._init_views()

        self._show_first_available()

    def _build_sidebar(self):
        panel = QFrame()
        panel.setFixedWidth(200)
        panel.setStyleSheet(f"""
            QFrame {{
                background: {COLOR_SIDEBAR};
                border-right: 1px solid {COLOR_BORDER};
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 24, 0, 20)
        layout.setSpacing(0)

        title = QLabel(APP_NAME)
        title.setStyleSheet(f"""
            font-size: 16px; font-weight: 600; color: {COLOR_TEXT};
            padding: 0 16px;
            margin-bottom: 8px;
        """)
        layout.addWidget(title)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {COLOR_BORDER}; border: none; margin: 0 16px;")
        layout.addWidget(sep)

        user_info = current_user()
        if user_info:
            uname = QLabel(f"{user_info.get('username', '')}  ({user_info.get('role_name', '')})")
            uname.setStyleSheet(f"""
                font-size: 10px; color: {COLOR_TEXT_MUTED};
                padding: 8px 16px;
            """)
            layout.addWidget(uname)

        for section_name, items in NAV_SECTIONS:
            visible_items = [(k, lbl, ic) for k, lbl, ic in items if has_permission(k)]
            if not visible_items:
                continue

            sec = SidebarSection(section_name)
            layout.addWidget(sec)

            for perm_key, label, icon in visible_items:
                btn = NavButton(label, icon)
                idx = len(self.nav_btns)
                btn.clicked.connect(lambda checked, i=idx, b=btn: self._navigate(i, b))
                self.nav_btns.append(btn)
                self.nav_keys.append(perm_key)
                layout.addWidget(btn)

        layout.addStretch()

        sep2 = QFrame()
        sep2.setFixedHeight(1)
        sep2.setStyleSheet(f"background: {COLOR_BORDER}; border: none; margin: 0 16px;")
        layout.addWidget(sep2)

        logout_btn = QPushButton("  \u00bb  Cerrar Sesion")
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                text-align: left; padding: 0 16px 0 15px;
                border: none; font-size: 12px; font-weight: 400;
                color: {COLOR_TEXT_DIM}; background: transparent; height: 36px;
            }}
            QPushButton:hover {{
                background: {COLOR_SIDEBAR_HOVER};
                color: {COLOR_TEXT};
            }}
        """)
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.clicked.connect(self._do_logout)
        layout.addWidget(logout_btn)

        ver = QLabel(f"v{APP_VERSION}")
        ver.setStyleSheet(f"""
            font-size: 10px; color: {COLOR_TEXT_DIM};
            padding: 12px 16px;
        """)
        layout.addWidget(ver)

        return panel

    def _init_views(self):
        for perm_key in self.nav_keys:
            view_class = VIEW_CLASSES[perm_key]
            view = view_class(self)
            self.view_widgets.append(view)
            self.stack.addWidget(view)

    def _show_first_available(self):
        if self.nav_btns:
            self._navigate(0, self.nav_btns[0])

    def _navigate(self, index, btn=None):
        for b in self.nav_btns:
            b.set_active(False)
        if btn:
            btn.set_active(True)
        elif index < len(self.nav_btns):
            self.nav_btns[index].set_active(True)

        self.stack.setCurrentIndex(index)
        if index < len(self.view_widgets):
            if hasattr(self.view_widgets[index], "refresh"):
                self.view_widgets[index].refresh()

    def refresh_stats(self):
        if self.view_widgets and hasattr(self.view_widgets[0], "refresh"):
            self.view_widgets[0].refresh()

    def _do_logout(self):
        logout()
        self.close()
