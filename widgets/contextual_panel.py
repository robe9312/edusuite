from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QStackedWidget,
)
from PySide6.QtCore import Qt

from config import (
    COLOR_PANEL, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_TEXT_MUTED,
    COLOR_BORDER, COLOR_ACCENT, COLOR_HOVER, COLOR_SURFACE,
)


class PanelPage:
    def build(self, layout):
        raise NotImplementedError


class ContextualPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(0)
        self._stack = QStackedWidget()
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._stack.setStyleSheet(f"background: {COLOR_PANEL};")
        layout.addWidget(self._stack)

        self.setStyleSheet(f"""
            ContextualPanel {{
                border-left: 1px solid {COLOR_BORDER};
                background: {COLOR_PANEL};
            }}
        """)

    def show_page(self, page_widget):
        self._stack.addWidget(page_widget)
        self._stack.setCurrentWidget(page_widget)
        self.setFixedWidth(300)

    def hide_panel(self):
        self.setFixedWidth(0)

    def is_visible(self):
        return self.width() > 0


class StudentPanelPage(QWidget):
    def __init__(self, student_data, close_callback=None):
        super().__init__()
        self._data = student_data
        self._close_cb = close_callback
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        top = QHBoxLayout()
        if self._close_cb:
            close_btn = QPushButton("\u2716")
            close_btn.setFixedSize(28, 28)
            close_btn.setCursor(Qt.PointingHandCursor)
            close_btn.setStyleSheet(f"""
                QPushButton {{ border: none; background: transparent;
                    color: {COLOR_TEXT_MUTED}; font-size: 14px; }}
                QPushButton:hover {{ color: {COLOR_TEXT}; background: {COLOR_HOVER}; }}
            """)
            close_btn.clicked.connect(self._close_cb)
            top.addStretch()
            top.addWidget(close_btn)
        layout.addLayout(top)

        name_lbl = QLabel(self._data.get("nombre", ""))
        name_lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLOR_TEXT};")
        layout.addWidget(name_lbl)

        sections = [
            ("Código", self._data.get("code", "-")),
            ("Curso", self._data.get("course", "-")),
            ("Tutor", self._data.get("tutor", "-")),
        ]
        for label, value in sections:
            row = QHBoxLayout()
            row.setSpacing(8)
            k = QLabel(label)
            k.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
            k.setFixedWidth(60)
            v = QLabel(str(value))
            v.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 12px;")
            row.addWidget(k)
            row.addWidget(v)
            row.addStretch()
            layout.addLayout(row)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {COLOR_BORDER};")
        layout.addWidget(sep)

        for title in ("Notas", "Observaciones", "Historial"):
            lbl = QLabel(title)
            lbl.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 13px; font-weight: bold; margin-top: 4px;")
            layout.addWidget(lbl)
            content = QLabel("Sin datos")
            content.setWordWrap(True)
            content.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
            layout.addWidget(content)

        layout.addStretch()
