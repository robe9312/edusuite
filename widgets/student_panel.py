from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea,
)
from PySide6.QtCore import Qt

from config import (
    COLOR_PANEL, COLOR_SURFACE, COLOR_TEXT, COLOR_TEXT_DIM,
    COLOR_TEXT_MUTED, COLOR_BORDER, COLOR_ACCENT, COLOR_HOVER,
)


class StudentPanel(QFrame):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(0)
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.content = QWidget()
        self.content.setStyleSheet(f"background: {COLOR_PANEL};")
        cl = QVBoxLayout(self.content)
        cl.setContentsMargins(16, 16, 16, 16)
        cl.setSpacing(12)

        top = QHBoxLayout()
        self.close_btn = QPushButton("\u2716")
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                border: none; background: transparent; color: {COLOR_TEXT_MUTED};
                font-size: 14px;
            }}
            QPushButton:hover {{ color: {COLOR_TEXT}; background: {COLOR_HOVER}; }}
        """)
        top.addStretch()
        top.addWidget(self.close_btn)
        cl.addLayout(top)

        self.name_lbl = QLabel()
        self.name_lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLOR_TEXT};")
        cl.addWidget(self.name_lbl)

        fields = [
            ("Código", "code"),
            ("Tutor", "tutor"),
            ("Curso", "course"),
        ]
        self._field_labels = {}
        for label, key in fields:
            row = QHBoxLayout()
            row.setSpacing(8)
            k = QLabel(label)
            k.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
            k.setFixedWidth(60)
            v = QLabel("-")
            v.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 12px;")
            self._field_labels[key] = v
            row.addWidget(k)
            row.addWidget(v)
            row.addStretch()
            cl.addLayout(row)

        sep1 = QFrame()
        sep1.setFixedHeight(1)
        sep1.setStyleSheet(f"background: {COLOR_BORDER};")
        cl.addWidget(sep1)

        sections = [
            ("Notas", "notas"),
            ("Observaciones", "observaciones"),
            ("Historial", "historial"),
        ]
        self._section_labels = {}
        for title, key in sections:
            lbl = QLabel(title)
            lbl.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 13px; font-weight: bold; margin-top: 4px;")
            cl.addWidget(lbl)
            content = QLabel("Sin datos")
            content.setWordWrap(True)
            content.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
            self._section_labels[key] = content
            cl.addWidget(content)

        cl.addStretch()

        scroll = QScrollArea()
        scroll.setWidget(self.content)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
        """)
        layout.addWidget(scroll)

        self.setStyleSheet(f"""
            StudentPanel {{
                border-left: 1px solid {COLOR_BORDER};
                background: {COLOR_PANEL};
            }}
        """)

    def show_student(self, student_data):
        self.name_lbl.setText(student_data.get("nombre", ""))
        self._field_labels["code"].setText(student_data.get("code", "-"))
        self._field_labels["tutor"].setText(student_data.get("tutor", "-"))
        self._field_labels["course"].setText(student_data.get("course", "-"))
        self.setFixedWidth(280)

    def hide_panel(self):
        self.setFixedWidth(0)

    def is_visible(self):
        return self.width() > 0
