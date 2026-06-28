from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QRect, QEasingCurve, QTimer
from PySide6.QtGui import QPixmap
import os
from config import COLOR_SURFACE, COLOR_ACCENT, COLOR_ACCENT_HOVER, COLOR_TEXT, COLOR_TEXT_DIM, COLOR_BORDER, COLOR_HOVER
from settings_manager import get as get_setting

COLLAPSED_W = 72
EXPANDED_W = 200
ANIM_DURATION = 180

NAV_ITEMS = [
    ("inicio", "\U0001f3e0", "Inicio"),
    ("dashboard", "\U0001f4ca", "Dashboard"),
    ("notas", "\U0001f4da", "Notas"),
    ("estudiantes", "\U0001f9d1\u200d\U0001f393", "Estudiantes"),
    ("docentes", "\U0001f468\u200d\U0001f3eb", "Docentes"),
    ("asignaturas", "\U0001f4dd", "Asignaturas"),
    ("matricula", "\U0001f4bc", "Matrícula"),
    ("gastos", "\U0001f4b0", "Gastos"),
    ("editor", "\U0001f4c1", "Documentos"),
    ("backup", "\u26a0\ufe0f", "Backup"),
    ("configuracion", "\u2699\ufe0f", "Configuración"),
]


class SidebarButton(QPushButton):
    def __init__(self, icon_char, text, collapsed=True):
        super().__init__()
        self._icon_char = icon_char
        self._label = text
        self._collapsed = collapsed
        self.setFixedHeight(48)
        self.setCursor(Qt.PointingHandCursor)
        self._build()

    def _build(self):
        display = self._icon_char if self._collapsed else f"{self._icon_char}  {self._label}"
        self.setText(display)
        self.setStyleSheet(f"""
            QPushButton {{
                text-align: left; padding: 0 16px; border: none;
                color: {COLOR_TEXT_DIM}; font-size: 16px;
                background: transparent;
            }}
            QPushButton:hover {{
                background: {COLOR_HOVER}; color: {COLOR_TEXT};
                border-left: 3px solid {COLOR_ACCENT};
            }}
        """)

    def set_collapsed(self, collapsed):
        self._collapsed = collapsed
        self._build()

    def set_active(self, active):
        if active:
            self.setStyleSheet(f"""
                QPushButton {{
                    text-align: left; padding: 0 16px; border: none;
                    color: {COLOR_ACCENT}; font-size: 16px;
                    background: {COLOR_HOVER};
                    border-left: 3px solid {COLOR_ACCENT};
                }}
                QPushButton:hover {{
                    background: {COLOR_HOVER}; color: {COLOR_ACCENT};
                }}
            """)
        else:
            self._build()


class CompactSidebar(QWidget):
    page_changed = Signal(str)

    def __init__(self):
        super().__init__()
        self._expanded = False
        self._buttons = []
        self._current_page = "inicio"
        self.setFixedWidth(COLLAPSED_W)
        self._build()
        self.setAttribute(Qt.WA_Hover, True)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 16, 0, 16)
        layout.setSpacing(2)

        # Load institution logo if configured
        logo_path = get_setting('institution_logo_path')
        logo = QLabel()
        if logo_path and os.path.isfile(logo_path):
            pix = QPixmap(logo_path).scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo.setPixmap(pix)
        else:
            logo.setText("\U0001f393")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedHeight(48)
        logo.setStyleSheet(f"font-size: 24px; color: {COLOR_ACCENT};")
        layout.addWidget(logo)

        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {COLOR_BORDER}; margin: 8px 12px;")
        layout.addWidget(sep)

        for key, icon, label in NAV_ITEMS:
            btn = SidebarButton(icon, label, collapsed=True)
            btn.clicked.connect(lambda _, k=key: self._navigate(k))
            self._buttons.append((key, btn))
            layout.addWidget(btn)

        layout.addStretch()

        self.setStyleSheet(f"""
            CompactSidebar {{
                background: {COLOR_SURFACE};
                border-right: 1px solid {COLOR_BORDER};
            }}
        """)

    def _navigate(self, key):
        self._current_page = key
        for k, btn in self._buttons:
            btn.set_active(k == key)
        self.page_changed.emit(key)

    def add_custom_item(self, key, icon, label):
        btn = SidebarButton(icon, label, collapsed=True)
        btn.clicked.connect(lambda _, k=key: self._navigate(k))
        self._buttons.append((key, btn))
        self.layout().addWidget(btn)
        NAV_ITEMS.append((key, icon, label))

    def set_active_page(self, key):
        self._current_page = key
        for k, btn in self._buttons:
            btn.set_active(k == key)

    def enterEvent(self, event):
        self._animate(EXPANDED_W)

    def leaveEvent(self, event):
        self._animate(COLLAPSED_W)

    def _animate(self, target_w):
        self.anim = QPropertyAnimation(self, b"geometry")
        current = self.geometry()
        self.anim.setDuration(ANIM_DURATION)
        self.anim.setStartValue(current)
        self.anim.setEndValue(QRect(current.x(), current.y(), target_w, current.height()))
        self.anim.setEasingCurve(QEasingCurve.OutCubic)
        self.anim.finished.connect(lambda: self._on_anim_done(target_w))
        self.anim.start()

    def _on_anim_done(self, w):
        self.setFixedWidth(w)
        self._expanded = w > 100
        for _, btn in self._buttons:
            btn.set_collapsed(not self._expanded)
