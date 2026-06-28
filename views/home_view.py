from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from datetime import date

from config import *
import settings_manager as sset
from services import ServiceRegistry


class _SummaryCard(QFrame):
    def __init__(self, icon, label, value):
        super().__init__()
        self.setFixedSize(180, 110)
        self.setStyleSheet(f"""
            _SummaryCard {{
                background: {COLOR_PANEL};
                border: 1px solid {COLOR_BORDER};
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(4)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 22px;")
        lay.addWidget(icon_lbl)

        val = QLabel(str(value))
        val.setStyleSheet(f"font-size: 24px; font-weight: 700; color: {COLOR_TEXT};")
        lay.addWidget(val)

        lbl = QLabel(label)
        lbl.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_DIM};")
        lay.addWidget(lbl)


class _QuickActionButton(QPushButton):
    def __init__(self, icon, text):
        super().__init__(f"{icon}  {text}")
        self.setFixedHeight(56)
        self.setMinimumWidth(180)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_PANEL};
                border: 1px solid {COLOR_BORDER};
                color: {COLOR_TEXT};
                font-size: 14px;
                text-align: left;
                padding: 0 20px;
            }}
            QPushButton:hover {{
                background: {COLOR_HOVER};
                border-color: {COLOR_ACCENT};
            }}
        """)


class _NoticeItem(QFrame):
    def __init__(self, icon, text, detail="", urgent=False):
        super().__init__()
        self.setStyleSheet(f"""
            _NoticeItem {{
                background: transparent;
                border-bottom: 1px solid {COLOR_BORDER};
            }}
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(12)

        ic = QLabel(icon)
        ic.setStyleSheet(f"font-size: 16px;")
        lay.addWidget(ic)

        txt = QLabel(text)
        txt.setStyleSheet(f"font-size: 13px; color: {COLOR_TEXT};")
        lay.addWidget(txt, 1)

        if detail:
            det = QLabel(detail)
            det.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_DIM};")
            lay.addWidget(det)

        if urgent:
            dot = QLabel("●")
            dot.setStyleSheet(f"font-size: 10px; color: {COLOR_DANGER};")
            lay.addWidget(dot)


class _FooterItem(QLabel):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_DIM};")


class HomeView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        root = QVBoxLayout(container)
        root.setContentsMargins(48, 40, 48, 40)
        root.setSpacing(0)

        self._build_hero(root)
        root.addSpacing(32)
        self._build_quick_actions(root)
        root.addSpacing(32)
        self._build_summary(root)
        root.addSpacing(32)
        self._build_notices(root)
        root.addSpacing(32)
        self._build_footer(root)
        root.addStretch()

        scroll.setWidget(container)
        layout.addWidget(scroll)

    # ── Hero ──────────────────────────────────────────────────────

    def _build_hero(self, root):
        block = QFrame()
        block.setStyleSheet(f"background: {COLOR_PANEL}; border: 1px solid {COLOR_BORDER};")
        lay = QVBoxLayout(block)
        lay.setContentsMargins(32, 28, 32, 28)
        lay.setAlignment(Qt.AlignCenter)

        logo_path = sset.get("institution_logo_path")
        logo_lbl = QLabel()
        logo_lbl.setFixedSize(80, 80)
        logo_lbl.setAlignment(Qt.AlignCenter)
        if logo_path:
            pix = QPixmap(logo_path)
            if not pix.isNull():
                logo_lbl.setPixmap(pix.scaled(76, 76, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            else:
                logo_lbl.setText("🏫")
                logo_lbl.setStyleSheet("font-size: 48px;")
        else:
            logo_lbl.setText("🏫")
            logo_lbl.setStyleSheet("font-size: 48px;")

        center = QVBoxLayout()
        center.setAlignment(Qt.AlignCenter)
        center.setSpacing(4)

        logo_hl = QHBoxLayout()
        logo_hl.setAlignment(Qt.AlignCenter)
        logo_hl.addWidget(logo_lbl)
        center.addLayout(logo_hl)

        name = sset.get("institution_name", "EduSuite")
        title = QLabel(name)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size: 28px; font-weight: 700; color: {COLOR_TEXT};")
        center.addWidget(title)

        code = sset.get("institution_code", "")
        if code:
            code_lbl = QLabel(f"Código: {code}")
            code_lbl.setAlignment(Qt.AlignCenter)
            code_lbl.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_MUTED};")
            center.addWidget(code_lbl)

        director = sset.get("institution_director", "")
        if director:
            dir_lbl = QLabel(f"Director/a: {director}")
            dir_lbl.setAlignment(Qt.AlignCenter)
            dir_lbl.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_MUTED};")
            center.addWidget(dir_lbl)

        year_badge = QLabel("Año Escolar 2025-2026")
        year_badge.setAlignment(Qt.AlignCenter)
        year_badge.setStyleSheet(f"""
            color: {COLOR_ACCENT}; font-size: 11px; font-weight: 600;
            padding: 3px 10px;
            border: 1px solid {COLOR_ACCENT};
            max-width: 200px;
        """)
        year_hl = QHBoxLayout()
        year_hl.setAlignment(Qt.AlignCenter)
        year_hl.addWidget(year_badge)
        center.addLayout(year_hl)

        lay.addLayout(center)
        root.addWidget(block)

    # ── Quick actions ────────────────────────────────────────────

    def _build_quick_actions(self, root):
        hdr = QLabel("Acciones rápidas")
        hdr.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {COLOR_TEXT_MUTED}; margin-bottom: 12px;")
        root.addWidget(hdr)

        row = QHBoxLayout()
        row.setSpacing(12)

        actions = [
            ("📄", "Nuevo documento", self._new_document),
            ("📂", "Abrir documentos", lambda: self.main._navigate("editor")),
            ("👤", "Registrar estudiante", lambda: self.main._navigate("estudiantes")),
            ("👨‍🏫", "Registrar docente", lambda: self.main._navigate("docentes")),
            ("🖨", "Imprimir", self._print_placeholder),
            ("⚙", "Configuración", lambda: self.main._navigate("configuracion")),
        ]

        for icon, text, callback in actions:
            btn = _QuickActionButton(icon, text)
            btn.clicked.connect(callback)
            row.addWidget(btn)

        root.addLayout(row)

    # ── Summary cards ────────────────────────────────────────────

    def _build_summary(self, root):
        hdr = QLabel("Resumen del centro")
        hdr.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {COLOR_TEXT_MUTED}; margin-bottom: 12px;")
        root.addWidget(hdr)

        try:
            stats = ServiceRegistry.instance().statistics()
            data = stats.dashboard_data()
        except Exception:
            data = {}

        cards_data = [
            ("👨‍🎓", "Estudiantes", data.get("total_students", 0)),
            ("👩‍🏫", "Docentes", data.get("total_teachers", 0)),
            ("📄", "Documentos", data.get("total_documents", 0)),
            ("📋", "Asistencia Hoy", "—"),
            ("📈", "Promedio General", "—"),
        ]

        row = QHBoxLayout()
        row.setSpacing(12)
        for icon, label, value in cards_data:
            row.addWidget(_SummaryCard(icon, label, value))
        row.addStretch()
        root.addLayout(row)

    # ── Notices panel ────────────────────────────────────────────

    def _build_notices(self, root):
        hdr = QLabel("Avisos")
        hdr.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {COLOR_TEXT_MUTED}; margin-bottom: 8px;")
        root.addWidget(hdr)

        panel = QFrame()
        panel.setStyleSheet(f"background: {COLOR_PANEL}; border: 1px solid {COLOR_BORDER};")
        panel.setFixedHeight(40 + 36 * 6)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        items = [
            ("📝", "Próximos exámenes", "Ninguno programado"),
            ("💾", "Backups pendientes", "Al día"),
            ("📌", "Documentos sin guardar", "Ninguno"),
            ("👤", "Estudiantes nuevos", "0 esta semana"),
            ("🎂", "Cumpleaños", "Ninguno hoy"),
            ("✉", "Mensajes", "0 sin leer"),
        ]

        for icon, text, detail in items:
            lay.addWidget(_NoticeItem(icon, text, detail))

        root.addWidget(panel)

    # ── Footer ───────────────────────────────────────────────────

    def _build_footer(self, root):
        foot = QFrame()
        foot.setStyleSheet(f"background: transparent; border-top: 1px solid {COLOR_BORDER};")
        lay = QHBoxLayout(foot)
        lay.setContentsMargins(0, 16, 0, 8)
        lay.setSpacing(20)

        try:
            from db.database import get_stats
            db_stats = get_stats()
            last_backup = db_stats.get("last_backup", "—")
        except Exception:
            last_backup = "—"

        today = date.today().strftime("%d/%m/%Y")

        lay.addWidget(_FooterItem(f"💾 Último respaldo: {last_backup}"))
        lay.addWidget(_FooterItem(f"Versión {APP_VERSION}"))
        lay.addWidget(_FooterItem("Licencia: Uso educativo"))
        lay.addStretch()
        lay.addWidget(_FooterItem(f"📅 {today}"))

        root.addWidget(foot)

    def _new_document(self):
        if "editor" in self.main._view_widgets:
            mgr = self.main._view_widgets["editor"]
            if hasattr(mgr, "_new_document"):
                mgr._new_document()
            else:
                self.main._navigate("editor")

    def _print_placeholder(self):
        pass

    def refresh(self):
        pass
