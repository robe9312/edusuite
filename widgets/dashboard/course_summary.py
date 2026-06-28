from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QGridLayout
from PySide6.QtCore import Qt
from config import *
from .base import DashboardWidget


class CourseMiniCard(QFrame):
    def __init__(self, course, enrolled, approved, failed, rate):
        super().__init__()
        self.setFixedSize(180, 130)
        color = COLOR_SUCCESS if rate >= 50 else (COLOR_WARNING if rate >= 30 else COLOR_DANGER)
        self.setStyleSheet(f"""
            background: {COLOR_SURFACE};
            border: 1px solid {COLOR_BORDER};
            border-top: 3px solid {color};
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(2)

        name = QLabel(course)
        name.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px; font-weight: 600;")
        layout.addWidget(name)

        row = QHBoxLayout()
        row.setSpacing(12)

        col1 = QVBoxLayout()
        col1.setSpacing(1)
        m = QLabel("👥")
        m.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px;")
        col1.addWidget(m)
        mv = QLabel(str(enrolled))
        mv.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 16px; font-weight: bold;")
        col1.addWidget(mv)
        ml = QLabel("Matriculados")
        ml.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 9px;")
        col1.addWidget(ml)
        row.addLayout(col1)

        col2 = QVBoxLayout()
        col2.setSpacing(1)
        a = QLabel("✅")
        a.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px;")
        col2.addWidget(a)
        av = QLabel(str(approved))
        av.setStyleSheet(f"color: {COLOR_SUCCESS}; font-size: 16px; font-weight: bold;")
        col2.addWidget(av)
        al = QLabel("Aprobados")
        al.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 9px;")
        col2.addWidget(al)
        row.addLayout(col2)

        col3 = QVBoxLayout()
        col3.setSpacing(1)
        r = QLabel("❌")
        r.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px;")
        col3.addWidget(r)
        rv = QLabel(str(failed))
        rv.setStyleSheet(f"color: {COLOR_DANGER}; font-size: 16px; font-weight: bold;")
        col3.addWidget(rv)
        rl = QLabel("Reprobados")
        rl.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 9px;")
        col3.addWidget(rl)
        row.addLayout(col3)

        layout.addLayout(row)

        rate_lbl = QLabel(f"{rate}%")
        rate_lbl.setStyleSheet(f"""
            color: {color}; font-size: 14px; font-weight: bold;
        """)
        layout.addWidget(rate_lbl)


class CourseSummaryWidget(DashboardWidget):
    WIDGET_ID = "course_summary"

    def __init__(self, parent=None):
        super().__init__("Distribución por curso", parent)
        self._body = QFrame()
        self._grid = QGridLayout(self._body)
        self._grid.setContentsMargins(16, 16, 16, 16)
        self._grid.setSpacing(12)
        self.set_content(self._body)

    def update_data(self, data: dict):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        courses = data.get("courses", [])
        for i, c in enumerate(courses):
            enrolled = c.get("enrolled", 0)
            ev = c.get("evaluated", 0)
            approved = c.get("approved", 0)
            failed = c.get("failed", 0)
            rate = round(approved / ev * 100, 1) if ev else 0
            card = CourseMiniCard(c["curso"], enrolled, approved, failed, rate)
            self._grid.addWidget(card, i // 4, i % 4)
