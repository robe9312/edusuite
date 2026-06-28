from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from config import *
from .base import DashboardWidget


class FeedItem(QFrame):
    def __init__(self, icon, title, subtitle=""):
        super().__init__()
        self.setFixedHeight(40)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        ic = QLabel(icon)
        ic.setStyleSheet("font-size: 14px;")
        ic.setFixedWidth(20)
        layout.addWidget(ic)

        vl = QVBoxLayout()
        vl.setSpacing(1)
        t = QLabel(title)
        t.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px;")
        vl.addWidget(t)
        if subtitle:
            s = QLabel(subtitle)
            s.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 10px;")
            vl.addWidget(s)
        layout.addLayout(vl, 1)


class ActivityFeedWidget(DashboardWidget):
    WIDGET_ID = "activity_feed"

    def __init__(self, parent=None):
        super().__init__("Últimos movimientos", parent)
        self._body = QFrame()
        self._layout = QVBoxLayout(self._body)
        self._layout.setContentsMargins(16, 12, 16, 12)
        self._layout.setSpacing(6)
        self.set_content(self._body)

    def update_data(self, data: dict):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        activity = data.get("activity", [])
        for entry in activity:
            t = entry.get("type", "")
            if t == "grade":
                self._layout.addWidget(FeedItem(
                    "✔", f"{entry.get('student', '')} - {entry.get('subject', '')}",
                    f"{entry.get('period', '')} · Nota: {entry.get('score', '—')}"
                ))
            elif t == "enrollment":
                self._layout.addWidget(FeedItem(
                    "➕", f"Nueva matrícula: {entry.get('student', '')}",
                    f"Curso: {entry.get('curso', '')}"
                ))

        self._layout.addStretch()
