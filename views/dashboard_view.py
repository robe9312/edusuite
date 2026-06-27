from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
)
from PySide6.QtCore import Qt

from db.database import get_stats, get_db_path
from config import *
from ui_style import Panel, Header, Separator


class StatBlock(QFrame):
    def __init__(self, label, value):
        super().__init__()
        self.setStyleSheet(f"""
            StatBlock {{
                background: {COLOR_PANEL};
            }}
        """)
        self.setMinimumSize(180, 80)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        self.num = QLabel(str(value))
        self.num.setStyleSheet(f"""
            font-size: 28px; font-weight: 600; color: {COLOR_TEXT};
        """)
        layout.addWidget(self.num)

        self.lbl = QLabel(label)
        self.lbl.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_MUTED}; letter-spacing: 0.5px;")
        layout.addWidget(self.lbl)

    def set_value(self, value):
        self.num.setText(str(value))


class DashboardView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        h = Header("Panel de control")
        layout.addWidget(h)

        blocks = QHBoxLayout()
        blocks.setSpacing(0)

        self.student_block = StatBlock("ESTUDIANTES ACTIVOS", 0)
        blocks.addWidget(self.student_block, 1)

        vsep = QFrame()
        vsep.setFixedWidth(1)
        vsep.setStyleSheet(f"background: {COLOR_BORDER}; border: none;")
        blocks.addWidget(vsep)

        self.teacher_block = StatBlock("PROFESORES", 0)
        blocks.addWidget(self.teacher_block, 1)

        vsep2 = QFrame()
        vsep2.setFixedWidth(1)
        vsep2.setStyleSheet(f"background: {COLOR_BORDER}; border: none;")
        blocks.addWidget(vsep2)

        self.subject_block = StatBlock("ASIGNATURAS", 0)
        blocks.addWidget(self.subject_block, 1)

        vsep3 = QFrame()
        vsep3.setFixedWidth(1)
        vsep3.setStyleSheet(f"background: {COLOR_BORDER}; border: none;")
        blocks.addWidget(vsep3)

        self.grade_block = StatBlock("NOTAS REGISTRADAS", 0)
        blocks.addWidget(self.grade_block, 1)

        layout.addLayout(blocks)

        info_panel = Panel()
        il = info_panel.layout()

        it = QLabel("Informacion del sistema")
        it.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {COLOR_TEXT};")
        il.addWidget(it)

        self.db_label = QLabel(f"Base de datos: {get_db_path()}")
        self.db_label.setStyleSheet(f"""
            font-size: 11px; color: {COLOR_TEXT_MUTED};
            padding: 6px 10px;
            background: {COLOR_INPUT};
            border: 1px solid {COLOR_BORDER};
        """)
        self.db_label.setWordWrap(True)
        il.addWidget(self.db_label)

        self.stat_detail = QLabel("")
        self.stat_detail.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_MUTED};")
        il.addWidget(self.stat_detail)

        layout.addWidget(info_panel)

        ver = QLabel(f"v{APP_VERSION}")
        ver.setStyleSheet(f"font-size: 10px; color: {COLOR_TEXT_DIM};")
        ver.setAlignment(Qt.AlignRight)
        layout.addStretch()
        layout.addWidget(ver)

    def refresh(self):
        try:
            s = get_stats()
            self.student_block.set_value(s["students"])
            self.teacher_block.set_value(s["teachers"])
            self.subject_block.set_value(s["subjects"])
            self.grade_block.set_value(s["grades"])
            self.db_label.setText(f"Base de datos: {get_db_path()}")
            self.stat_detail.setText(
                f"{s['students']} estudiantes  |  {s['teachers']} docentes  |  "
                f"{s['subjects']} asignaturas  |  {s['grades']} notas"
            )
        except Exception as e:
            self.stat_detail.setText(f"Error: {e}")
