from PySide6.QtCore import Qt, Signal, QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableView, QHeaderView, QFrame, QTabBar, QStackedWidget,
)
from config import (
    COLOR_SURFACE, COLOR_BG, COLOR_PANEL, COLOR_BORDER,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_ACCENT, COLOR_ACCENT_HOVER,
    COLOR_HOVER, COLOR_TEXT_DIM, COLOR_SIDEBAR_ACTIVE,
)
from spreadsheet.services import DocumentService
from spreadsheet.core.grid_cell import CellType
from spreadsheet.engine import SpreadsheetEngine
from spreadsheet.datasource.memory_source import MemoryDataSource


class EngineSheetModel(QAbstractTableModel):
    def __init__(self, engine):
        super().__init__()
        self._engine = engine

    def rowCount(self, parent=QModelIndex()):
        return self._engine.row_count() if self._engine else 0

    def columnCount(self, parent=QModelIndex()):
        return self._engine.col_count() if self._engine else 0

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not self._engine:
            return None
        cell = self._engine.get_cell(index.row(), index.column())
        if role == Qt.DisplayRole:
            return cell.display
        if role == Qt.ForegroundRole:
            return None
        return None

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            from string import ascii_uppercase
            label = ""
            n = section
            while n >= 0:
                label = ascii_uppercase[n % 26] + label
                n = n // 26 - 1
            return label
        return str(section + 1)

    def refresh(self):
        self.beginResetModel()
        self.endResetModel()


class WorkbookRenderView(QWidget):
    edit_requested = Signal(str)
    delete_requested = Signal(str)

    def __init__(self, section, doc_service=None, parent=None):
        super().__init__(parent)
        self.section = section
        self._doc_service = doc_service or DocumentService()
        self._models = []
        self._engines = []

        doc_name = section.get("name", "")
        if doc_name:
            docs = self._doc_service.list_documents(search=doc_name)
            if docs:
                opened = self._doc_service.open(docs[0]["id"])
            else:
                opened = False
            if not opened and "doc_id" in section:
                opened = self._doc_service.open(section["doc_id"])
        else:
            opened = False
        self._engines = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        toolbar = self._build_toolbar()
        layout.addWidget(toolbar)

        if not opened or not self._doc_service.adapter.sheet_count():
            empty = QLabel("Esta seccion no tiene datos de workbook")
            empty.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; padding: 40px;")
            empty.setAlignment(Qt.AlignCenter)
            layout.addWidget(empty)
            return

        self.stack = QStackedWidget()
        num_sheets = self._doc_service.adapter.sheet_count()
        for i in range(num_sheets):
            grid = self._doc_service.adapter.sheet(i)
            engine = SpreadsheetEngine(
                grid,
                MemoryDataSource(grid.row_count(), grid.col_count())
            )
            self._engines.append(engine)
            model = EngineSheetModel(engine)
            self._models.append(model)

            tv = QTableView()
            tv.setModel(model)
            tv.setAlternatingRowColors(True)
            tv.setSelectionBehavior(QTableView.SelectRows)
            tv.setEditTriggers(QTableView.NoEditTriggers)
            tv.horizontalHeader().setStretchLastSection(True)
            tv.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
            tv.verticalHeader().setDefaultSectionSize(28)
            tv.verticalHeader().setVisible(False)
            tv.setStyleSheet(f"""
                QTableView {{
                    background: {COLOR_SURFACE}; border: 1px solid {COLOR_BORDER};
                    gridline-color: {COLOR_BORDER}; color: {COLOR_TEXT};
                    font-size: 12px; outline: none;
                }}
                QTableView::item {{ padding: 4px 8px; }}
                QTableView::item:selected {{
                    background: {COLOR_ACCENT}44; color: {COLOR_TEXT};
                }}
                QHeaderView::section {{
                    background: {COLOR_PANEL}; color: {COLOR_TEXT_MUTED};
                    font-weight: 600; padding: 6px 8px;
                    border: none; border-bottom: 1px solid {COLOR_BORDER};
                    font-size: 11px;
                }}
            """)
            self.stack.addWidget(tv)

        layout.addWidget(self.stack)

        if num_sheets > 1:
            self.tabs = QTabBar()
            self.tabs.setStyleSheet(f"""
                QTabBar {{
                    background: {COLOR_PANEL}; border: none; border-radius: 6px;
                    padding: 2px;
                }}
                QTabBar::tab {{
                    padding: 6px 16px; color: {COLOR_TEXT_MUTED};
                    font-size: 12px; border: none; border-radius: 4px;
                    margin: 2px;
                }}
                QTabBar::tab:selected {{
                    background: {COLOR_SURFACE}; color: {COLOR_TEXT};
                    font-weight: 600;
                }}
            """)
            for i in range(num_sheets):
                meta = self._doc_service.adapter.sheet_meta(i)
                self.tabs.addTab(meta.get("name", f"Sheet {i+1}"))
            self.tabs.currentChanged.connect(self._on_tab_change)
            layout.addWidget(self.tabs)

    def _on_tab_change(self, idx):
        self.stack.setCurrentIndex(idx)

    def _build_toolbar(self):
        bar = QFrame()
        bar.setStyleSheet(f"QFrame {{ background: {COLOR_PANEL}; border-radius: 8px; }}")
        h = QHBoxLayout(bar)
        h.setContentsMargins(16, 8, 16, 8)

        sec = self.section
        color = sec.get("color", "#5e81f4")
        icon = sec.get("icon", "📄")

        dot = QLabel()
        dot.setFixedSize(12, 12)
        dot.setStyleSheet(f"background: {color}; border-radius: 6px;")
        h.addWidget(dot)

        name = sec.get("name", "Seccion")
        title = QLabel(f"{icon} {name}")
        title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {COLOR_TEXT};")
        h.addWidget(title)

        stype = sec.get("type", "spreadsheet")
        badge = QLabel(stype)
        badge.setStyleSheet(f"""
            background: {color}33; color: {color};
            font-size: 11px; padding: 2px 10px; border-radius: 10px; font-weight: 600;
        """)
        h.addWidget(badge)

        desc = sec.get("description", "")
        if desc:
            d = QLabel(desc)
            d.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
            h.addWidget(d)

        h.addStretch()

        sc = self._doc_service.adapter.sheet_count()
        sc_lbl = QLabel(f"{sc} hoja(s)")
        sc_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px; margin-right: 8px;")
        h.addWidget(sc_lbl)

        btn = QPushButton("Editar en LuckySheet")
        btn.setStyleSheet(f"""
            QPushButton {{ padding: 0 16px; height: 34px; border: none;
                background: {COLOR_ACCENT}; color: #fff; font-size: 13px; border-radius: 6px;
                font-weight: 600; }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        btn.clicked.connect(lambda: self.edit_requested.emit(sec.get("section_key", "")))
        h.addWidget(btn)

        btn_del = QPushButton("Eliminar")
        btn_del.setStyleSheet("""
            QPushButton { padding: 0 12px; height: 34px; border: none;
                background: transparent; color: #ef4444; font-size: 12px; border-radius: 6px; }
            QPushButton:hover { background: #2a1a1a; }
        """)
        btn_del.clicked.connect(lambda: self.delete_requested.emit(sec.get("section_key", "")))
        h.addWidget(btn_del)

        return bar

    def refresh_model(self):
        for m in self._models:
            m.refresh()
        for i, e in enumerate(self._engines):
            grid = self._doc_service.adapter.sheet(i)
            if grid:
                e._grid = grid
        for m in self._models:
            m.refresh()

    @classmethod
    def from_data(cls, doc_service, doc_name="Documento", parent=None):
        sec = {
            "section_key": f"preview_{id(doc_service)}",
            "name": doc_name,
            "icon": "\U0001f4c4",
            "type": "spreadsheet",
        }
        return cls(sec, doc_service, parent)
