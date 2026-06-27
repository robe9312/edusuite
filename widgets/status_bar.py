from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

from config import COLOR_SURFACE, COLOR_TEXT_MUTED, COLOR_BORDER, COLOR_SUCCESS, COLOR_ACCENT


class StatusBar(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(28)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(20)

        parts = [
            ("\u25cf  Conectado", COLOR_SUCCESS),
            ("SQLite", COLOR_ACCENT),
        ]
        for text, color in parts:
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color: {color}; font-size: 11px;")
            layout.addWidget(lbl)

        layout.addStretch()

        self.school_year_lbl = QLabel()
        self.school_year_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(self.school_year_lbl)

        self.last_saved_lbl = QLabel()
        self.last_saved_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(self.last_saved_lbl)

        self.user_lbl = QLabel()
        self.user_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        layout.addWidget(self.user_lbl)

        self.setStyleSheet(f"""
            StatusBar {{
                background: {COLOR_SURFACE};
                border-top: 1px solid {COLOR_BORDER};
            }}
        """)

    def update_user(self, username):
        self.user_lbl.setText(f"Usuario: {username}")

    def update_school_year(self, year):
        self.school_year_lbl.setText(f"Año escolar {year}")

    def update_last_saved(self, time_str):
        self.last_saved_lbl.setText(f"Último guardado {time_str}")
