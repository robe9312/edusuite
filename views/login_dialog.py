from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame,
)
from PySide6.QtCore import Qt

from config import *
from ui_style import Input, Button
from db.database import authenticate
from session import login


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — Iniciar sesión")
        self.setFixedSize(380, 320)
        self.setStyleSheet(f"""
            QDialog {{
                background: {COLOR_BG};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        title = QLabel(APP_NAME)
        title.setStyleSheet(f"""
            font-size: 22px; font-weight: 600; color: {COLOR_TEXT};
        """)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Sistema de Gestion Escolar")
        subtitle.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_DIM}; letter-spacing: 1px;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {COLOR_BORDER}; border: none;")
        layout.addWidget(sep)

        layout.addSpacing(8)

        self.user_input = Input("Usuario")
        layout.addWidget(self.user_input)

        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Contraseña")
        self.pass_input.setEchoMode(QLineEdit.Password)
        self.pass_input.setStyleSheet(f"""
            QLineEdit {{
                padding: 0 12px;
                height: 36px;
                border: 1px solid {COLOR_BORDER};
                background: {COLOR_INPUT};
                color: {COLOR_TEXT};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {COLOR_ACCENT};
            }}
            QLineEdit:hover {{
                border-color: {COLOR_TEXT_MUTED};
            }}
        """)
        layout.addWidget(self.pass_input)

        self.error_label = QLabel("")
        self.error_label.setStyleSheet(f"font-size: 11px; color: {COLOR_DANGER};")
        layout.addWidget(self.error_label)

        login_btn = QPushButton("Ingresar")
        login_btn.setStyleSheet(f"""
            QPushButton {{
                height: 36px;
                border: none;
                background: {COLOR_ACCENT};
                color: #ffffff;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {COLOR_ACCENT_HOVER};
            }}
        """)
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.clicked.connect(self._do_login)
        layout.addWidget(login_btn)

        self.user_input.returnPressed.connect(self._do_login)
        self.pass_input.returnPressed.connect(self._do_login)

        self.user_input.setFocus()

    def _do_login(self):
        username = self.user_input.text().strip()
        password = self.pass_input.text().strip()

        if not username or not password:
            self.error_label.setText("Ingrese usuario y contraseña")
            return

        user = authenticate(username, password)
        if user is None:
            self.error_label.setText("Usuario o contraseña incorrectos")
            return

        login(user)
        self.accept()
