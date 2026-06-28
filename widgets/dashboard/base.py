from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from config import *


class DashboardWidget(QFrame):
    WIDGET_ID = "base"

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._collapsed = False
        self._title = title
        self._content: QFrame = None

        self.setStyleSheet(f"""
            DashboardWidget {{
                background: {COLOR_PANEL};
                border: 1px solid {COLOR_BORDER};
            }}
        """)

        self._outer = QVBoxLayout(self)
        self._outer.setContentsMargins(0, 0, 0, 0)
        self._outer.setSpacing(0)

        self._build_header()
        self._separator = QFrame()
        self._separator.setFixedHeight(1)
        self._separator.setStyleSheet(f"background: {COLOR_BORDER}; border: none;")
        self._outer.addWidget(self._separator)

    def _build_header(self):
        hdr = QFrame()
        hdr.setFixedHeight(40)
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(16, 0, 8, 0)

        icon = QLabel("▣")
        icon.setStyleSheet(f"color: {COLOR_ACCENT}; font-size: 12px;")
        hl.addWidget(icon)

        self._title_lbl = QLabel(self._title)
        self._title_lbl.setStyleSheet(f"""
            color: {COLOR_TEXT}; font-size: 13px; font-weight: 600;
        """)
        hl.addWidget(self._title_lbl, 1)

        self._toggle_btn = QPushButton("−")
        self._toggle_btn.setFixedSize(24, 24)
        self._toggle_btn.setCursor(Qt.PointingHandCursor)
        self._toggle_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {COLOR_TEXT_MUTED};
                border: 1px solid {COLOR_BORDER};
                font-size: 14px; font-weight: bold;
            }}
            QPushButton:hover {{
                background: {COLOR_HOVER}; color: {COLOR_TEXT};
            }}
        """)
        self._toggle_btn.clicked.connect(self._toggle)
        hl.addWidget(self._toggle_btn)

        self._outer.addWidget(hdr)

    def _toggle(self):
        self._collapsed = not self._collapsed
        if self._content:
            self._content.setVisible(not self._collapsed)
            self._separator.setVisible(not self._collapsed)
        self._toggle_btn.setText("+" if self._collapsed else "−")

    def set_content(self, widget: QFrame):
        self._content = widget
        self._outer.addWidget(widget, 1)

    def widget_id(self) -> str:
        return self.WIDGET_ID
