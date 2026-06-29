from PySide6.QtCore import Qt, Signal, QAbstractTableModel, QModelIndex
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableView, QHeaderView, QFrame, QTabBar, QStackedWidget,
)
from config import (
    COLOR_SURFACE, COLOR_BG, COLOR_PANEL, COLOR_BORDER,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_ACCENT, COLOR_ACCENT_HOVER,
    COLOR_HOVER, COLOR_TEXT_DIM, COLOR_SIDEBAR_ACTIVE, COLOR_DANGER,
)
from logs.logger import log as log_msg
from spreadsheet.services import DocumentService
from spreadsheet.core.grid_cell import CellType
from spreadsheet.engine import SpreadsheetEngine
from spreadsheet.datasource.memory_source import MemoryDataSource


def _active_area(grid):
    max_r = max_c = -1
    for r in range(grid.row_count()):
        for c in range(grid.col_count()):
            cell = grid.cell(r, c)
            val = cell.display if hasattr(cell, 'display') else str(cell)
            if val and val.strip():
                if r > max_r: max_r = r
                if c > max_c: max_c = c
    if max_r < 0:
        return 1, 1
    return max_r + 1, max_c + 1


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
        if cell is None:
            return None
        if role == Qt.DisplayRole:
            return cell.display if cell.display else None
        if role == Qt.ForegroundRole:
            from PySide6.QtGui import QColor
            fg = cell.style.text_color if cell.style else None
            if fg and hasattr(fg, 'to_qt'):
                return QColor(*fg.to_qt())
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
        self._content_widget = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        toolbar = self._build_toolbar()
        layout.addWidget(toolbar)

        self._body_layout = layout
        self._load_content()

    def _load_content(self):
        if self._content_widget:
            self._body_layout.removeWidget(self._content_widget)
            self._content_widget.deleteLater()
            self._content_widget = None
        self._models.clear()
        self._engines.clear()

        sec_name = self.section.get("name", "?")
        doc_id = self.section.get("document_id")
        log_msg(f"VIEW_LOAD section={sec_name} doc_id={doc_id}")
        if doc_id:
            opened = self._doc_service.open(doc_id)
            log_msg(f"VIEW_OPEN doc_id={doc_id} opened={opened}")
        else:
            doc_name = self.section.get("name", "")
            if doc_name:
                docs = self._doc_service.list_documents(search=doc_name)
                if docs:
                    log_msg(f"VIEW_FIND doc_id={docs[0]['id']} via name={doc_name}")
                    opened = self._doc_service.open(docs[0]["id"])
                else:
                    log_msg(f"VIEW_NO_DOC no doc found for name={doc_name}")
                    opened = False
            else:
                opened = False

        num_sheets = self._doc_service.adapter.sheet_count()
        log_msg(f"VIEW_SHEETS count={num_sheets} after open")

        if not opened or not num_sheets:
            log_msg(f"VIEW_EMPTY section={sec_name} doc_id={doc_id}")
            empty = QLabel("Esta seccion no tiene datos de workbook")
            empty.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; padding: 40px;")
            empty.setAlignment(Qt.AlignCenter)
            self._content_widget = empty
            self._body_layout.addWidget(empty)
            return

        container = QWidget()
        cl = QVBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(8)

        stack = QStackedWidget()
        for i in range(num_sheets):
            grid = self._doc_service.adapter.sheet(i)
            rows, cols = _active_area(grid)
            log_msg(f"VIEW_SHEET{i} active_area rows={rows} cols={cols}")
            engine = SpreadsheetEngine(
                grid,
                MemoryDataSource(rows, cols)
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
            stack.addWidget(tv)

        cl.addWidget(stack)

        if num_sheets > 1:
            tabs = QTabBar()
            tabs.setStyleSheet(f"""
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
                tabs.addTab(meta.get("name", f"Sheet {i+1}"))
            tabs.currentChanged.connect(stack.setCurrentIndex)
            cl.addWidget(tabs)

        self._content_widget = container
        self._body_layout.addWidget(container)

    def refresh(self):
        name = self.section.get("name", "?")
        log_msg(f"VIEW_REFRESH section={name}")
        self._load_content()

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

        title = QLabel(sec.get("name", ""))
        title.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {COLOR_TEXT};")
        h.addWidget(title)

        h.addStretch()

        btn = QPushButton("Editar plantilla")
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_ACCENT}; color: #fff;
                border: none; padding: 6px 16px;
                font-weight: 600; font-size: 12px;
            }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        btn.clicked.connect(lambda: self.edit_requested.emit(sec.get("section_key", "")))
        h.addWidget(btn)

        btn_del = QPushButton("Archivar")
        btn_del.setCursor(Qt.PointingHandCursor)
        btn_del.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {COLOR_DANGER};
                border: 1px solid {COLOR_DANGER};
                padding: 6px 16px; font-size: 12px;
            }}
            QPushButton:hover {{ background: {COLOR_DANGER}15; }}
        """)
        btn_del.clicked.connect(lambda: self.delete_requested.emit(sec.get("section_key", "")))
        h.addWidget(btn_del)

        return bar
