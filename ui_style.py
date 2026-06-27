from PySide6.QtWidgets import QPushButton, QLineEdit, QComboBox, QTableWidget, QFrame, QLabel
from PySide6.QtCore import Qt
from config import *


def apply_global_style(app):
    app.setStyleSheet(f"""
        * {{
            font-family: {BODY_FONT};
            font-size: 13px;
        }}
        QToolTip {{
            background: {COLOR_PANEL};
            color: {COLOR_TEXT};
            border: 1px solid {COLOR_BORDER};
            padding: 4px 8px;
            font-size: 11px;
        }}
        QScrollBar:vertical {{
            background: {COLOR_BG};
            width: 6px;
            margin: 0;
        }}
        QScrollBar::handle:vertical {{
            background: {COLOR_BORDER};
            min-height: 30px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {COLOR_TEXT_DIM};
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0;
        }}
        QScrollBar:horizontal {{
            background: {COLOR_BG};
            height: 6px;
            margin: 0;
        }}
        QScrollBar::handle:horizontal {{
            background: {COLOR_BORDER};
            min-width: 30px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {COLOR_TEXT_DIM};
        }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0;
        }}
    """)


class Button(QPushButton):
    def __init__(self, text="", variant="primary"):
        super().__init__(text)
        self.setCursor(Qt.PointingHandCursor)
        bg = COLOR_ACCENT
        bg_h = COLOR_ACCENT_HOVER
        txt = "#ffffff"
        h = 36
        if variant == "success":
            bg = COLOR_SUCCESS
            bg_h = "#5a7e5a"
        elif variant == "danger":
            bg = COLOR_DANGER
            bg_h = "#904040"
        elif variant == "ghost":
            bg = "transparent"
            bg_h = COLOR_HOVER
            txt = COLOR_TEXT
        self.setStyleSheet(f"""
            QPushButton {{
                padding: 0 16px;
                height: {h}px;
                border: none;
                background: {bg};
                color: {txt};
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background: {bg_h};
            }}
            QPushButton:pressed {{
                background: {bg_h};
            }}
            QPushButton:disabled {{
                color: {COLOR_TEXT_DIM};
                background: {COLOR_INPUT};
            }}
        """)


class Input(QLineEdit):
    def __init__(self, placeholder=""):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setStyleSheet(f"""
            QLineEdit {{
                padding: 0 12px;
                height: 36px;
                border: 1px solid {COLOR_BORDER};
                background: {COLOR_INPUT};
                color: {COLOR_TEXT};
                font-size: 13px;
                selection-background-color: {COLOR_SURFACE};
            }}
            QLineEdit:focus {{
                border-color: {COLOR_ACCENT};
            }}
            QLineEdit:hover {{
                border-color: {COLOR_TEXT_MUTED};
            }}
        """)


class Combo(QComboBox):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"""
            QComboBox {{
                padding: 0 12px;
                height: 36px;
                border: 1px solid {COLOR_BORDER};
                background: {COLOR_INPUT};
                color: {COLOR_TEXT};
                font-size: 13px;
                min-width: 100px;
            }}
            QComboBox:hover {{
                border-color: {COLOR_TEXT_MUTED};
            }}
            QComboBox:focus {{
                border-color: {COLOR_ACCENT};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                width: 0;
                height: 0;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 5px solid {COLOR_TEXT_MUTED};
            }}
            QComboBox QAbstractItemView {{
                background: {COLOR_SURFACE};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                selection-background-color: {COLOR_SIDEBAR_ACTIVE};
                selection-color: {COLOR_TEXT};
                padding: 2px 0;
                outline: none;
            }}
            QComboBox QAbstractItemView::item {{
                padding: 6px 12px;
            }}
            QComboBox QAbstractItemView::item:hover {{
                background: {COLOR_HOVER};
            }}
        """)


class Table(QTableWidget):
    def __init__(self):
        super().__init__()
        self.setAlternatingRowColors(False)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setShowGrid(False)
        self.verticalHeader().setDefaultSectionSize(34)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setDefaultSectionSize(100)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setFixedHeight(32)

        self.setStyleSheet(f"""
            QTableWidget {{
                background: transparent;
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                font-size: 13px;
                outline: none;
            }}
            QTableWidget::item {{
                padding: 4px 12px;
                border-bottom: 1px solid {COLOR_BORDER};
            }}
            QTableWidget::item:selected {{
                background: {COLOR_SIDEBAR_ACTIVE};
                color: {COLOR_TEXT};
            }}
            QTableWidget::item:hover {{
                background: {COLOR_HOVER};
            }}
            QHeaderView::section {{
                background: {COLOR_SURFACE};
                color: {COLOR_TEXT_MUTED};
                padding: 4px 12px;
                border: none;
                border-bottom: 1px solid {COLOR_BORDER};
                border-right: 1px solid {COLOR_BORDER};
                font-family: {HEADER_FONT};
                font-weight: 400;
                font-size: 10px;
                letter-spacing: 1.5px;
                text-transform: uppercase;
            }}
            QHeaderView::section:last {{
                border-right: none;
            }}
        """)


class Separator(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedHeight(1)
        self.setStyleSheet(f"background: {COLOR_BORDER}; border: none;")


class Panel(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"""
            Panel {{
                background: {COLOR_PANEL};
                border: 1px solid {COLOR_BORDER};
            }}
        """)

    def layout(self):
        if getattr(self, "_vlayout", None) is None:
            from PySide6.QtWidgets import QVBoxLayout
            self._vlayout = QVBoxLayout(self)
            self._vlayout.setContentsMargins(16, 12, 16, 12)
            self._vlayout.setSpacing(8)
        return self._vlayout


class Header(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {COLOR_TEXT};
        """)
