from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout
from PySide6.QtCore import Qt
from config import *
from .base import DashboardWidget


def heatmap_emoji(pct):
    if pct >= 70:
        return "🟢"
    elif pct >= 50:
        return "🟡"
    elif pct >= 30:
        return "🟠"
    return "🔴"


class HeatmapWidget(DashboardWidget):
    WIDGET_ID = "heatmap"

    def __init__(self, parent=None):
        super().__init__("Tasa de aprobación", parent)
        self._body = QFrame()
        self._grid = QVBoxLayout(self._body)
        self._grid.setContentsMargins(16, 12, 16, 12)
        self._grid.setSpacing(8)
        self.set_content(self._body)

    def update_data(self, data: dict):
        while self._grid.count():
            item = self._grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        courses = data.get("courses", [])
        for c in courses:
            ev = c.get("evaluated", 0)
            approved = c.get("approved", 0)
            pct = round(approved / ev * 100, 1) if ev else 0

            row = QHBoxLayout()
            row.setSpacing(12)

            emoji = QLabel(heatmap_emoji(pct))
            emoji.setStyleSheet("font-size: 16px;")
            emoji.setFixedWidth(28)
            row.addWidget(emoji)

            name = QLabel(c["curso"])
            name.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px;")
            name.setFixedWidth(90)
            row.addWidget(name)

            bar_bg = QFrame()
            bar_bg.setFixedHeight(14)
            bar_bg.setStyleSheet(f"background: {COLOR_INPUT}; border-radius: 3px;")
            bar_layout = QHBoxLayout(bar_bg)
            bar_layout.setContentsMargins(0, 0, 0, 0)

            fill_w = max(int(200 * pct / 100), 4)
            fill = QFrame()
            fill.setFixedWidth(fill_w)
            fill.setFixedHeight(14)
            c1 = "#d32f2f" if pct < 30 else ("#f9a825" if pct < 50 else ("#66bb6a" if pct < 70 else "#26a69a"))
            fill.setStyleSheet(f"background: {c1}; border-radius: 3px;")
            bar_layout.addWidget(fill)
            bar_layout.addStretch()
            row.addWidget(bar_bg, 1)

            pct_lbl = QLabel(f"{pct}%")
            pct_lbl.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px; font-weight: 600;")
            pct_lbl.setFixedWidth(50)
            row.addWidget(pct_lbl)

            self._grid.addLayout(row)
