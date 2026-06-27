from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
from PySide6.QtCore import Qt

from db.database import get_stats, get_db_path
from config import *
from widgets.card import StatCard


class ProgressBar(QFrame):
    def __init__(self, label, value, max_val, color=COLOR_ACCENT):
        super().__init__()
        self.setFixedHeight(36)
        self._value = value
        self._max = max_val if max_val > 0 else 1
        self._color = color

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 11px;")
        lbl.setFixedWidth(100)
        layout.addWidget(lbl)

        bar_bg = QFrame()
        bar_bg.setFixedHeight(8)
        bar_bg.setStyleSheet(f"background: {COLOR_INPUT}; border-radius: 4px;")
        bg_layout = QVBoxLayout(bar_bg)
        bg_layout.setContentsMargins(0, 0, 0, 0)

        pct = min(self._value / self._max, 1.0)
        fill = QFrame()
        fill.setFixedWidth(int(200 * pct))
        fill.setFixedHeight(8)
        fill.setStyleSheet(f"background: {self._color}; border-radius: 4px;")
        bg_layout.addWidget(fill)
        layout.addWidget(bar_bg, 1)

        val_lbl = QLabel(str(value))
        val_lbl.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 12px;")
        val_lbl.setFixedWidth(40)
        layout.addWidget(val_lbl)


class DashboardView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        header = QLabel("Dashboard")
        header.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {COLOR_TEXT};")
        layout.addWidget(header)

        cards = QHBoxLayout()
        cards.setSpacing(16)

        self.student_card = StatCard("—", "Estudiantes", "Matriculados", COLOR_ACCENT)
        cards.addWidget(self.student_card)

        self.teacher_card = StatCard("—", "Docentes", "Activos", "#5E81F4")
        cards.addWidget(self.teacher_card)

        self.pass_card = StatCard("—", "Aprobados", "Global", COLOR_SUCCESS)
        cards.addWidget(self.pass_card)

        self.avg_card = StatCard("—", "Promedio", "General", "#F5B942")
        cards.addWidget(self.avg_card)

        layout.addLayout(cards)

        grid = QHBoxLayout()
        grid.setSpacing(16)

        left_panel = QFrame()
        left_panel.setStyleSheet(f"background: {COLOR_PANEL};")
        lp = QVBoxLayout(left_panel)
        lp.setContentsMargins(20, 16, 20, 16)
        lp.setSpacing(12)

        lh = QLabel("Distribución por curso")
        lh.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 14px; font-weight: 600;")
        lp.addWidget(lh)

        self.course_stats_widget = QVBoxLayout()
        lp.addLayout(self.course_stats_widget)
        lp.addStretch()

        grid.addWidget(left_panel, 1)

        right_panel = QFrame()
        right_panel.setStyleSheet(f"background: {COLOR_PANEL};")
        rp = QVBoxLayout(right_panel)
        rp.setContentsMargins(20, 16, 20, 16)
        rp.setSpacing(12)

        rh = QLabel("Información del sistema")
        rh.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 14px; font-weight: 600;")
        rp.addWidget(rh)

        self.db_label = QLabel(f"Base de datos: {get_db_path()}")
        self.db_label.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        self.db_label.setWordWrap(True)
        rp.addWidget(self.db_label)

        self.stat_detail = QLabel("")
        self.stat_detail.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
        rp.addWidget(self.stat_detail)

        rp.addStretch()
        grid.addWidget(right_panel, 1)

        layout.addLayout(grid)

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def refresh(self):
        try:
            s = get_stats()
            self.student_card.set_value(s["students"])
            self.teacher_card.set_value(s["teachers"])

            grade_count = max(s.get("grades", 0), 1)
            pass_count = int(s.get("passed", grade_count * 0.7))
            pass_pct = round(pass_count / grade_count * 100, 1) if grade_count else 0
            self.pass_card.set_value(f"{pass_pct}%")

            avg = round(s.get("avg_grade", 7.5), 1)
            self.avg_card.set_value(avg)

            self._clear_layout(self.course_stats_widget)
            course_data = s.get("course_distribution", {})
            if course_data:
                max_count = max(course_data.values()) if course_data else 1
                for course_name, count in sorted(course_data.items()):
                    bar = ProgressBar(course_name, count, max_count, COLOR_ACCENT)
                    self.course_stats_widget.addWidget(bar)
                self.course_stats_widget.addStretch()

            self.db_label.setText(f"Base de datos: {get_db_path()}")
            self.stat_detail.setText(
                f"{s['students']} estudiantes  |  {s['teachers']} docentes  |  "
                f"{s['subjects']} asignaturas  |  {s['grades']} notas"
            )
        except Exception as e:
            self.stat_detail.setText(f"Error: {e}")
