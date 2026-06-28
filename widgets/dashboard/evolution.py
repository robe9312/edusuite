from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt
from config import *
from .base import DashboardWidget


class EvolutionBar(QFrame):
    def __init__(self, label, pct, max_pct, color=COLOR_ACCENT):
        super().__init__()
        self.setFixedHeight(28)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 11px;")
        lbl.setFixedWidth(80)
        layout.addWidget(lbl)

        bar_bg = QFrame()
        bar_bg.setFixedHeight(16)
        bar_bg.setStyleSheet(f"background: {COLOR_INPUT}; border-radius: 3px;")
        bar_layout = QHBoxLayout(bar_bg)
        bar_layout.setContentsMargins(0, 0, 0, 0)

        fill_w = max(int(200 * pct / max_pct), 4) if max_pct else 4
        fill = QFrame()
        fill.setFixedWidth(fill_w)
        fill.setFixedHeight(16)
        fill.setStyleSheet(f"background: {color}; border-radius: 3px;")
        bar_layout.addWidget(fill)
        bar_layout.addStretch()
        layout.addWidget(bar_bg, 1)

        pct_lbl = QLabel(f"{pct}%")
        pct_lbl.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px; font-weight: 600;")
        pct_lbl.setFixedWidth(50)
        layout.addWidget(pct_lbl)


class EvolutionWidget(DashboardWidget):
    WIDGET_ID = "evolution"

    def __init__(self, parent=None):
        super().__init__("Evolución por evaluación", parent)
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

        evolution = data.get("evolution", {})
        labels = {"T1": "Evaluación 1", "T2": "Evaluación 2", "T3": "Evaluación 3"}
        max_pct = max(
            (evolution[p].get("approved", 0) / max(evolution[p].get("total", 1), 1) * 100
             for p in ("T1", "T2", "T3") if evolution.get(p)),
            default=100
        )

        colors = {"T1": "#5E81F4", "T2": "#66BB6A", "T3": "#F5B942"}
        for p in ("T1", "T2", "T3"):
            ev = evolution.get(p, {})
            total = ev.get("total", 0)
            approved = ev.get("approved", 0)
            pct = round(approved / total * 100, 1) if total else 0
            self._layout.addWidget(EvolutionBar(
                labels[p], pct, max_pct, colors[p]
            ))

        self._layout.addStretch()
