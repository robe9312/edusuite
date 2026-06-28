from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QFrame, QMenu, QAction, QGridLayout, QMessageBox,
)
from PySide6.QtCore import Qt

from config import *
from services import ServiceRegistry
from widgets.dashboard import (
    KpiCardsWidget, CourseSummaryWidget, HeatmapWidget,
    AlertsWidget, ActivityFeedWidget, QuickActionsWidget,
    EvolutionWidget, DocumentsWidget,
)


class DashboardView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._stats = ServiceRegistry.instance().statistics()
        self._widgets = {}
        self._widget_layout = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"background: transparent;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self._root = QVBoxLayout(container)
        self._root.setContentsMargins(32, 28, 32, 28)
        self._root.setSpacing(0)

        self._build_header()
        self._build_widgets()
        self._root.addStretch()

        scroll.setWidget(container)
        layout.addWidget(scroll)

        self._load_settings()

    def _build_header(self):
        hdr = QFrame()
        hl = QHBoxLayout(hdr)
        hl.setContentsMargins(0, 0, 0, 20)

        title = QLabel("Dashboard")
        title.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {COLOR_TEXT};")
        hl.addWidget(title)

        hl.addStretch()

        year = QLabel("Curso 2025-2026")
        year.setStyleSheet(f"""
            color: {COLOR_TEXT_DIM}; font-size: 12px;
            padding: 4px 12px;
            border: 1px solid {COLOR_BORDER};
        """)
        hl.addWidget(year)

        self._gear_btn = QPushButton("⚙")
        self._gear_btn.setFixedSize(36, 36)
        self._gear_btn.setCursor(Qt.PointingHandCursor)
        self._gear_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_PANEL}; color: {COLOR_TEXT_MUTED};
                border: 1px solid {COLOR_BORDER};
                font-size: 16px;
            }}
            QPushButton:hover {{
                background: {COLOR_HOVER}; color: {COLOR_TEXT};
            }}
        """)
        self._gear_btn.clicked.connect(self._show_settings_menu)
        hl.addWidget(self._gear_btn)

        self._root.addWidget(hdr)

    def _build_widgets(self):
        grid = QGridLayout()
        grid.setSpacing(16)

        config = [
            ("kpi_cards", KpiCardsWidget, 0, 0),
            ("course_summary", CourseSummaryWidget, 1, 0),
            ("heatmap", HeatmapWidget, 2, 0),
            ("activity_feed", ActivityFeedWidget, 3, 0),
            ("alerts", AlertsWidget, 0, 1),
            ("evolution", EvolutionWidget, 1, 1),
            ("quick_actions", QuickActionsWidget, 2, 1),
            ("documents", DocumentsWidget, 3, 1),
        ]

        for wid_id, cls, row, col in config:
            if wid_id == "quick_actions":
                w = cls(self.main, self)
            elif wid_id == "documents":
                w = cls(self.main, self)
            else:
                w = cls(self)
            self._widgets[wid_id] = w
            grid.addWidget(w, row, col)

        grid.setColumnStretch(0, 3)
        grid.setColumnStretch(1, 2)
        self._grid = grid
        self._root.addLayout(grid)

    def _load_settings(self):
        import json
        from pathlib import Path
        layout_file = Path(__file__).parent.parent / "dashboard_layout.json"
        hidden = []
        try:
            if layout_file.exists():
                with open(layout_file) as f:
                    hidden = json.load(f).get("hidden", [])
        except Exception:
            pass
        for wid_id, w in self._widgets.items():
            w.setVisible(wid_id not in hidden)

    def _show_settings_menu(self):
        import json
        from pathlib import Path
        layout_file = Path(__file__).parent.parent / "dashboard_layout.json"

        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{
                background: {COLOR_SURFACE};
                color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                padding: 4px 0;
            }}
            QMenu::item {{
                padding: 8px 24px;
                font-size: 12px;
            }}
            QMenu::item:selected {{
                background: {COLOR_SIDEBAR_ACTIVE};
            }}
            QMenu::indicator {{
                width: 16px;
                height: 16px;
                margin-left: 4px;
            }}
        """)

        hidden = []
        try:
            if layout_file.exists():
                with open(layout_file) as f:
                    hidden = json.load(f).get("hidden", [])
        except Exception:
            pass
        hidden_set = set(hidden)

        labels = {
            "kpi_cards": "Indicadores principales",
            "course_summary": "Distribución por curso",
            "heatmap": "Tasa de aprobación",
            "alerts": "Alertas",
            "activity_feed": "Últimos movimientos",
            "evolution": "Evolución por evaluación",
            "quick_actions": "Acciones rápidas",
            "documents": "Documentos recientes",
        }

        for wid_id, label in labels.items():
            if wid_id not in self._widgets:
                continue
            a = QAction(f"  {label}", self)
            a.setCheckable(True)
            a.setChecked(wid_id not in hidden_set)
            a.setData(wid_id)
            a.triggered.connect(lambda checked, w=wid_id: self._toggle_widget(w))
            menu.addAction(a)

        menu.exec(self._gear_btn.mapToGlobal(
            self._gear_btn.rect().bottomRight()
        ))

    def _toggle_widget(self, wid_id):
        import json
        from pathlib import Path
        layout_file = Path(__file__).parent.parent / "dashboard_layout.json"

        w = self._widgets.get(wid_id)
        if not w:
            return

        visible = not w.isVisible()
        w.setVisible(visible)

        hidden = []
        try:
            if layout_file.exists():
                with open(layout_file) as f:
                    data = json.load(f)
                    hidden = data.get("hidden", [])
            else:
                data = {}
        except Exception:
            data = {}

        hidden_set = set(hidden)
        if visible:
            hidden_set.discard(wid_id)
        else:
            hidden_set.add(wid_id)
        data["hidden"] = list(hidden_set)
        try:
            with open(layout_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def refresh(self):
        if not self._stats:
            return
        try:
            data = self._stats.dashboard_data()
            for wid_id, w in self._widgets.items():
                if hasattr(w, "update_data"):
                    w.update_data(data)
        except Exception as e:
            QMessageBox.warning(self, "Dashboard", f"Error al cargar datos: {e}")
