from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from config import *
from .base import DashboardWidget


class AlertItem(QFrame):
    def __init__(self, icon, title, detail, color=COLOR_WARNING):
        super().__init__()
        self.setFixedHeight(52)
        self.setStyleSheet(f"""
            background: {COLOR_SURFACE};
            border-left: 3px solid {color};
        """)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(10)

        ic = QLabel(icon)
        ic.setStyleSheet(f"font-size: 16px;")
        ic.setFixedWidth(24)
        layout.addWidget(ic)

        vl = QVBoxLayout()
        vl.setSpacing(1)
        t = QLabel(title)
        t.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px; font-weight: 600;")
        vl.addWidget(t)
        d = QLabel(detail)
        d.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 11px;")
        vl.addWidget(d)
        layout.addLayout(vl, 1)


class AlertsWidget(DashboardWidget):
    WIDGET_ID = "alerts"

    def __init__(self, parent=None):
        super().__init__("Alertas", parent)
        self._body = QFrame()
        self._layout = QVBoxLayout(self._body)
        self._layout.setContentsMargins(16, 12, 16, 12)
        self._layout.setSpacing(8)
        self.set_content(self._body)

    def update_data(self, data: dict):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        courses = data.get("courses", [])
        subject_fails = data.get("subject_fails", [])

        worst_course = min(courses, key=lambda c: (
            c["approved"] / c["evaluated"] if c["evaluated"] else 1
        )) if courses else None

        if worst_course and worst_course.get("evaluated"):
            rate = round(worst_course["approved"] / worst_course["evaluated"] * 100, 1)
            self._layout.addWidget(AlertItem(
                "⚠", f"Curso con menor rendimiento: {worst_course['curso']}",
                f"Solo {rate}% de aprobados ({worst_course['approved']}/{worst_course['evaluated']})",
                COLOR_DANGER
            ))

        if subject_fails and subject_fails[0]["fails"] > 0:
            s = subject_fails[0]
            self._layout.addWidget(AlertItem(
                "📚", f"Asignatura crítica: {s['name']}",
                f"{s['fails']} suspensos de {s['total']} notas (media: {s['avg_score']})",
                COLOR_WARNING
            ))

        if worst_course and worst_course.get("enrolled", 0) > 0 and worst_course.get("evaluated", 0) < worst_course["enrolled"]:
            pending = worst_course["enrolled"] - worst_course["evaluated"]
            self._layout.addWidget(AlertItem(
                "👤", "Docentes",
                f"{pending} alumnos sin evaluar en {worst_course['curso']}",
                "#5E81F4"
            ))

        self._layout.addStretch()
