from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from config import *
from .base import DashboardWidget


class DocItem(QFrame):
    def __init__(self, name, doc_type, color="#5e81f4"):
        super().__init__()
        self.setFixedHeight(36)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            background: {COLOR_SURFACE};
            border: 1px solid {COLOR_BORDER};
            border-left: 3px solid {color};
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        n = QLabel(name)
        n.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px;")
        layout.addWidget(n, 1)

        t = QLabel(doc_type)
        t.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 10px;")
        layout.addWidget(t)


class DocumentsWidget(DashboardWidget):
    WIDGET_ID = "documents"

    def __init__(self, main_window=None, parent=None):
        super().__init__("Documentos recientes", parent)
        self._main = main_window
        self._body = QFrame()
        self._layout = QVBoxLayout(self._body)
        self._layout.setContentsMargins(16, 12, 16, 12)
        self._layout.setSpacing(6)
        self.set_content(self._body)
        self._load()

    def _load(self):
        if not self._main:
            return
        from db.database import get_all_custom_sections
        sections = get_all_custom_sections()
        for sec in sections[-5:]:
            name = sec.get("name", "Documento")
            doc_type = sec.get("type", "spreadsheet")
            color = sec.get("color", "#5e81f4")
            key = sec.get("section_key", "")
            item = DocItem(name, doc_type, color)
            item.mousePressEvent = lambda e, k=key: self._open(k)
            self._layout.addWidget(item)

        if not sections:
            empty = QLabel("Aún no hay documentos")
            empty.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 11px;")
            empty.setAlignment(Qt.AlignCenter)
            self._layout.addWidget(empty)

        self._layout.addStretch()

    def _open(self, section_key):
        if self._main and section_key in self._main._view_widgets:
            self._main._navigate(section_key)

    def update_data(self, data: dict):
        pass
