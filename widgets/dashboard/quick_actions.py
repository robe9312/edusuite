from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt
from config import *
from .base import DashboardWidget


class ActionButton(QPushButton):
    def __init__(self, text, emoji, color=COLOR_ACCENT):
        super().__init__(f"  {emoji}  {text}")
        self.setFixedHeight(44)
        self.setMinimumWidth(140)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                padding: 0 20px;
                border: 1px solid {COLOR_BORDER};
                background: {COLOR_SURFACE};
                color: {COLOR_TEXT};
                font-size: 12px;
                font-weight: 500;
                text-align: left;
            }}
            QPushButton:hover {{
                background: {color};
                color: #fff;
                border-color: {color};
            }}
        """)


class QuickActionsWidget(DashboardWidget):
    WIDGET_ID = "quick_actions"

    def __init__(self, main_window=None, parent=None):
        super().__init__("Acciones rápidas", parent)
        self._main = main_window
        self._build()

    def _build(self):
        body = QFrame()
        layout = QHBoxLayout(body)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        actions = [
            ("➕ Nueva matrícula", "enrollment"),
            ("📝 Registrar notas", "grades"),
            ("📤 Exportar Excel", "export"),
            ("📄 Generar boletines", "reports"),
            ("✏️ Abrir editor", "editor"),
            ("📁 Crear documento", "editor"),
        ]
        for text, action in actions:
            btn = ActionButton(text, "")
            btn.clicked.connect(lambda checked, a=action: self._on_action(a))
            layout.addWidget(btn)

        layout.addStretch()
        self.set_content(body)

    def _on_action(self, action):
        if not self._main:
            return
        if action == "export":
            if "grades" in self._main._view_widgets:
                self._main._navigate("grades")
                self._main._view_widgets["grades"]._export_dialog()
        elif action == "reports":
            self._main._navigate("grades")
        else:
            self._main._navigate(action)
