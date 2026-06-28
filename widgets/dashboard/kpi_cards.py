from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from config import *
from .base import DashboardWidget


class KpiCard(QFrame):
    def __init__(self, value, label, subtitle="", color=COLOR_ACCENT):
        super().__init__()
        self.setFixedSize(170, 110)
        self.setStyleSheet(f"""
            background: {COLOR_SURFACE};
            border: 1px solid {COLOR_BORDER};
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(2)

        self.val_lbl = QLabel(str(value))
        self.val_lbl.setStyleSheet(f"""
            font-size: 26px; font-weight: bold; color: {color};
        """)
        layout.addWidget(self.val_lbl)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 12px;")
        layout.addWidget(lbl)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px;")
            layout.addWidget(sub)

    def set_value(self, v):
        self.val_lbl.setText(str(v))


class KpiCardsWidget(DashboardWidget):
    WIDGET_ID = "kpi_cards"

    def __init__(self, parent=None):
        super().__init__("Indicadores principales", parent)
        self._cards = {}
        self._build()

    def _build(self):
        body = QFrame()
        layout = QHBoxLayout(body)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        kpis = [
            ("matriculados", "👨‍🎓 Matriculados", "Total", COLOR_ACCENT),
            ("evaluados", "📝 Evaluados", "Con notas", "#5E81F4"),
            ("aprobados", "✅ Aprobados", "Media ≥ 5", COLOR_SUCCESS),
            ("reprobados", "❌ Reprobados", "Media < 5", COLOR_DANGER),
            ("tasa", "📈 % Aprobación", "Global", "#F5B942"),
        ]
        for key, label, sub, color in kpis:
            card = KpiCard("—", label, sub, color)
            self._cards[key] = card
            layout.addWidget(card)

        layout.addStretch()
        self.set_content(body)

    def update_data(self, data: dict):
        self._cards["matriculados"].set_value(data.get("total_students", 0))
        self._cards["evaluados"].set_value(data.get("evaluated", 0))
        self._cards["aprobados"].set_value(data.get("approved", 0))
        self._cards["reprobados"].set_value(data.get("failed", 0))
        self._cards["tasa"].set_value(f"{data.get('pass_rate', 0)}%")
