from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QLineEdit, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
import webbrowser

from config import COLOR_SURFACE, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_TEXT_MUTED, COLOR_BORDER, COLOR_INPUT, COLOR_ACCENT


class HeaderBar(QWidget):
    search_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self.setFixedHeight(52)
        self._build()

    def _build(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(12)

        self.breadcrumb = QLabel("Inicio")
        self.breadcrumb.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(self.breadcrumb)

        layout.addStretch()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar...")
        self.search_input.setFixedWidth(220)
        self.search_input.setFixedHeight(32)
        self.search_input.textChanged.connect(self.search_changed.emit)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background: {COLOR_INPUT}; border: 1px solid {COLOR_BORDER};
                color: {COLOR_TEXT}; font-size: 12px; padding: 0 12px;
            }}
            QLineEdit:focus {{ border-color: {COLOR_ACCENT}; }}
        """)
        layout.addWidget(self.search_input)

        self.user_label = QLabel()
        self.user_label.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 12px;")
        layout.addWidget(self.user_label)
        # Button to open temporary web editor
        self.web_button = QPushButton("Editor Web")
        self.web_button.clicked.connect(lambda: webbrowser.open("http://localhost:5000"))
        layout.addWidget(self.web_button)

        self.setStyleSheet(f"""
            HeaderBar {{
                background: {COLOR_SURFACE};
                border-bottom: 1px solid {COLOR_BORDER};
            }}
        """)

    def set_breadcrumb(self, path):
        self.breadcrumb.setText(path)

    def set_user(self, username):
        self.user_label.setText(f"\U0001f464  {username}")
