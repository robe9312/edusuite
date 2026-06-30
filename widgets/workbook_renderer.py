from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableView, QFrame, QTabBar, QStackedWidget,
)
from config import (
    COLOR_SURFACE, COLOR_PANEL, COLOR_BORDER,
    COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_ACCENT, COLOR_ACCENT_HOVER,
    COLOR_DANGER,
)
from logs.logger import log as log_msg
from spreadsheet.services import DocumentService
from spreadsheet.renderer import WorkbookRenderer, SheetRenderer
from .formula_engine import FormulaEngine


class WorkbookRenderView(QWidget):
    edit_requested = Signal(str)
    delete_requested = Signal(str)

    def __init__(self, section, doc_service=None, parent=None):
        super().__init__(parent)
        self.section = section
        self._doc_service = doc_service or DocumentService()
        self._content_widget = None
        self._sheet_renderers: list = []
        self._tables: list = []
        self._engine: Optional[FormulaEngine] = None
        self._last_workbook_json: Optional[str] = None

        try:
            self._engine = FormulaEngine.instance()
        except Exception:
            self._engine = None

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
        self._sheet_renderers.clear()
        self._tables.clear()

        sec_name = self.section.get("name", "?")
        doc_id = self.section.get("document_id")
        log_msg(f"VIEW_LOAD section={sec_name} doc_id={doc_id}")
        if not doc_id:
            doc_name = self.section.get("name", "")
            if doc_name:
                docs = self._doc_service.list_documents(search=doc_name)
                if docs:
                    doc_id = docs[0]["id"]
                    log_msg(f"VIEW_FIND doc_id={doc_id} via name={doc_name}")

        workbook_json = None
        if doc_id:
            workbook_json = self._doc_service.latest_workbook(doc_id)
            log_msg(f"VIEW_OPEN doc_id={doc_id} wb_len={len(workbook_json) if workbook_json else 0}")

        container = QWidget()
        cl = QVBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(8)

        if not workbook_json:
            log_msg(f"VIEW_EMPTY section={sec_name} doc_id={doc_id}")
            empty = QLabel("Esta sección no tiene una plantilla Luckysheet asociada.")
            empty.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 14px; padding: 40px;")
            empty.setAlignment(Qt.AlignCenter)
            cl.addWidget(empty)
            self._content_widget = container
            self._body_layout.addWidget(container)
            return

        self._last_workbook_json = workbook_json
        if self._engine is not None:
            self._engine.load_workbook(workbook_json)

        renderer = WorkbookRenderer.from_json(workbook_json, theme="default")
        stack = renderer.render(parent=container)

        num_sheets = stack.count()
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
                page = stack.widget(i)
                name = getattr(page, "objectName", lambda: f"Sheet {i+1}")() or f"Sheet {i+1}"
                tabs.addTab(name)
            tabs.currentChanged.connect(stack.setCurrentIndex)
            cl.addWidget(tabs)
        cl.addWidget(stack)

        for i in range(num_sheets):
            page = stack.widget(i)
            if isinstance(page, QTableView):
                page.setStyleSheet(f"""
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
                page.cellChanged.connect(self._on_cell_edited)
                self._tables.append(page)
        self._content_widget = container
        self._body_layout.addWidget(container)

        if self._engine is not None:
            try:
                self._engine.cellsChanged.disconnect()
            except (TypeError, RuntimeError):
                pass
            self._engine.cellsChanged.connect(self._on_engine_changed)

    def _on_cell_edited(self, row: int, col: int) -> None:
        if self._engine is None:
            return
        table = self.sender()
        if table is None:
            return
        item = table.item(row, col)
        if item is None:
            return
        new_text = item.text()
        sheet_index = 0
        for i, t in enumerate(self._tables):
            if t is table:
                sheet_index = i
                break
        self._engine.set_cell(sheet_index, row, col, new_text)

    def _on_engine_changed(self, sheet_index: int, cells: list) -> None:
        if not cells:
            return
        if sheet_index < len(self._tables):
            table = self._tables[sheet_index]
            sr = getattr(table, "_sheet_renderer", None)
            if sr is not None:
                sr.update_cells(table, cells)

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

        btn_del = QPushButton("\u2716 Borrar")
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
