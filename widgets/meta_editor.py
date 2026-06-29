from __future__ import annotations
import json
from typing import Optional, Callable

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QMessageBox, QDialog, QLineEdit,
    QComboBox, QFormLayout, QDialogButtonBox, QTextEdit,
)
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView, QTableView

from config import *
from services import ServiceRegistry
from spreadsheet.services import DocumentService
from spreadsheet import SpreadsheetEngine, WorkbookAdapter, MemoryDataSource
from widgets.workbook_renderer import EngineSheetModel


def _active_area(grid):
    max_r = max_c = -1
    for r in range(grid.row_count()):
        for c in range(grid.col_count()):
            cell = grid.get_cell(r, c)
            if cell and cell.display and cell.display.strip():
                if r > max_r: max_r = r
                if c > max_c: max_c = c
    if max_r < 0:
        return 0, 0
    return max_r + 1, max_c + 1


class _SectionRow(QFrame):
    def __init__(self, doc: dict, doc_service: DocumentService,
                 on_edit: Callable, on_delete: Callable):
        super().__init__()
        self._doc = doc
        self._doc_service = doc_service
        self._on_edit = on_edit
        self._on_delete = on_delete

        self.setStyleSheet(f"""
            _SectionRow {{
                background: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        # Name row
        name_row = QHBoxLayout()
        icon = doc.get("icon", "\U0001f4c4")
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 18px;")
        name_row.addWidget(icon_lbl)

        name_lbl = QLabel(doc["name"])
        name_lbl.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {COLOR_TEXT};")
        name_row.addWidget(name_lbl)
        name_row.addStretch()
        lay.addLayout(name_row)

        # Preview
        self._preview = QVBoxLayout()
        self._preview.setSpacing(0)
        lay.addLayout(self._preview)
        self._load_preview()

        # Actions
        act_row = QHBoxLayout()
        act_row.setSpacing(8)

        edit_btn = QPushButton("Editar")
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_ACCENT}; color: #fff;
                border: none; padding: 4px 16px;
                font-size: 12px; font-weight: 600;
            }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        edit_btn.clicked.connect(lambda: self._on_edit(self._doc["id"]))
        act_row.addWidget(edit_btn)

        del_btn = QPushButton("Eliminar")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {COLOR_DANGER};
                border: 1px solid {COLOR_DANGER};
                padding: 4px 16px; font-size: 12px;
            }}
            QPushButton:hover {{ background: {COLOR_DANGER}15; }}
        """)
        del_btn.clicked.connect(lambda: self._on_delete(self._doc["id"]))
        act_row.addWidget(del_btn)

        act_row.addStretch()
        lay.addLayout(act_row)

    def _load_preview(self):
        wb_json = self._doc_service.latest_workbook(self._doc["id"])
        if not wb_json:
            empty = QLabel("(sin datos)")
            empty.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 11px; padding: 4px 0;")
            self._preview.addWidget(empty)
            return

        try:
            wb_data = json.loads(wb_json) if isinstance(wb_json, str) else wb_json
            adapter = WorkbookAdapter()
            adapter.load(wb_data)
            grid = adapter.sheet(0)
            if grid is None:
                raise ValueError("Sin hoja")
            rows, cols = _active_area(grid)
            if rows == 0 or cols == 0:
                empty = QLabel("(vacío)")
                empty.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 11px; padding: 4px 0;")
                self._preview.addWidget(empty)
                return

            source = MemoryDataSource(rows, cols)
            engine = SpreadsheetEngine(grid, source)
            model = EngineSheetModel(engine)

            tv = QTableView()
            tv.setModel(model)
            tv.setAlternatingRowColors(True)
            tv.setEditTriggers(QTableView.NoEditTriggers)
            tv.horizontalHeader().setStretchLastSection(True)
            tv.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
            tv.verticalHeader().setDefaultSectionSize(22)
            tv.verticalHeader().setVisible(False)
            tv.setMaximumHeight(min(rows * 24 + 28, 280))
            tv.setStyleSheet(f"""
                QTableView {{
                    background: {COLOR_PANEL}; border: 1px solid {COLOR_BORDER};
                    gridline-color: {COLOR_BORDER}; color: {COLOR_TEXT};
                    font-size: 11px; outline: none;
                }}
                QTableView::item {{ padding: 1px 6px; }}
                QHeaderView::section {{
                    background: {COLOR_SURFACE}; color: {COLOR_TEXT_DIM};
                    border: none; border-bottom: 1px solid {COLOR_BORDER};
                    padding: 2px 6px; font-size: 10px; font-weight: 600;
                }}
            """)
            self._preview.addWidget(tv)
        except Exception:
            err = QLabel("Error al cargar vista previa")
            err.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
            self._preview.addWidget(err)


class MetaEditorWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._doc_service: DocumentService = ServiceRegistry.instance().spreadsheet().doc_service
        self._categories: list = []
        self._rows: list[_SectionRow] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setStyleSheet(f"background: transparent;")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 12)

        title = QLabel("Meta Editor")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {COLOR_TEXT};")
        hl.addWidget(title)

        hl.addStretch()

        new_btn = QPushButton("+ Nueva sección")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_ACCENT}; color: #fff;
                border: none; padding: 6px 18px;
                font-weight: 600; font-size: 13px;
            }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        new_btn.clicked.connect(self._new_section)
        hl.addWidget(new_btn)

        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(8)
        self._list_layout.addStretch()

        scroll.setWidget(self._container)
        layout.addWidget(scroll, 1)

        self._load_categories()
        self.refresh()

    def _load_categories(self):
        self._categories = self._doc_service.get_categories()

    def refresh(self):
        for r in self._rows:
            r.deleteLater()
        self._rows.clear()

        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        docs = self._doc_service.list_documents()
        for doc in docs:
            row = _SectionRow(doc, self._doc_service, self._edit, self._delete)
            self._rows.append(row)
            self._list_layout.addWidget(row)

        if not docs:
            empty = QLabel("No hay secciones. Crea la primera con «+ Nueva sección».")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 13px; padding: 40px;")
            self._list_layout.addWidget(empty)

        self._list_layout.addStretch()

    def _edit(self, doc_id: int):
        self._doc_service.open(doc_id)
        from widgets.luckysheet_window import LuckySheetWindow
        import socket
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()

        from http.server import HTTPServer
        from views.editor_view import _Handler
        from engine.meta_engine import MetaEngine
        _Handler.engine = MetaEngine()
        srv = HTTPServer(("127.0.0.1", port), _Handler)
        import threading
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()

        ls_data = self._doc_service.adapter.save()
        meta = self._doc_service.meta
        import json, os
        DATA_FILE = "/tmp/edusuite_workbook.json"
        SAVE_FILE = "/tmp/edusuite_save.json"
        payload = {"sheetData": ls_data, "name": meta.get("name", "Documento")}
        with open(DATA_FILE, "w") as f:
            json.dump(payload, f)
        try:
            os.remove(SAVE_FILE)
        except FileNotFoundError:
            pass

        self._ls_window = LuckySheetWindow(port, self)
        self._ls_window.showMaximized()
        self._ls_window.destroyed.connect(self._on_editor_closed)

    def _on_editor_closed(self):
        self.refresh()

    def _delete(self, doc_id: int):
        doc = self._doc_service.meta if self._doc_service.current_id == doc_id else None
        name = doc.get("name", "sección") if doc else "sección"
        reply = QMessageBox.question(
            self, "Eliminar sección",
            f"¿Desea eliminar la sección?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self._doc_service.delete(doc_id)
        self.refresh()

    def _new_section(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Nueva sección")
        dlg.setMinimumWidth(380)
        dlg.setStyleSheet(f"background: {COLOR_SURFACE}; color: {COLOR_TEXT};")

        form = QFormLayout(dlg)
        form.setSpacing(8)
        form.setContentsMargins(16, 12, 16, 12)

        name_input = QLineEdit()
        name_input.setPlaceholderText("Nombre de la sección")
        name_input.setStyleSheet(f"""
            QLineEdit {{
                background: {COLOR_INPUT}; color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER}; padding: 6px;
            }}
        """)
        form.addRow("Nombre:", name_input)

        type_combo = QComboBox()
        type_combo.setStyleSheet(f"""
            QComboBox {{
                background: {COLOR_INPUT}; color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER}; padding: 6px;
            }}
        """)
        for cat in self._categories:
            type_combo.addItem(f"{cat.get('icon', '')}  {cat['name']}", cat["id"])
        form.addRow("Tipo:", type_combo)

        desc_input = QTextEdit()
        desc_input.setPlaceholderText("Descripción opcional")
        desc_input.setMaximumHeight(60)
        desc_input.setStyleSheet(f"""
            QTextEdit {{
                background: {COLOR_INPUT}; color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER}; padding: 4px;
            }}
        """)
        form.addRow("Descripción:", desc_input)

        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        btns.button(QDialogButtonBox.Ok).setText("Crear")
        form.addRow(btns)

        if dlg.exec() != QDialog.Accepted:
            return

        name = name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "El nombre es obligatorio.")
            return

        doc_id = self._doc_service.create(
            name=name,
            category_id=type_combo.currentData(),
            description=desc_input.toPlainText().strip(),
        )
        if doc_id:
            self.refresh()
            self._edit(doc_id)
