from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

from config import COLOR_PANEL, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_TEXT_MUTED, COLOR_BORDER


class StatCard(QFrame):
    def __init__(self, value, title, subtitle="", accent_color=None):
        super().__init__()
        self.setFixedSize(180, 120)
        self.setCursor(Qt.PointingHandCursor)
        self._accent = accent_color
        self._build(value, title, subtitle)

    def _build(self, value, title, subtitle):
        self.setStyleSheet(f"""
            StatCard {{
                background: {COLOR_PANEL};
                border: 1px solid {COLOR_BORDER};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)

        self.val_lbl = QLabel(str(value))
        self.val_lbl.setStyleSheet(f"""
            font-size: 28px; font-weight: bold;
            color: {self._accent or COLOR_TEXT};
        """)
        layout.addWidget(self.val_lbl)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 12px;")
        layout.addWidget(title_lbl)

        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px;")
            layout.addWidget(sub_lbl)

    def set_value(self, value):
        self.val_lbl.setText(str(value))
