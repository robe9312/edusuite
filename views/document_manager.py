from __future__ import annotations
import json
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QComboBox, QMessageBox,
    QDialog, QFormLayout, QDialogButtonBox, QTextEdit, QSizePolicy,
)
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView, QTableView

from config import *
from services import ServiceRegistry
from spreadsheet.services import DocumentService
from spreadsheet import MemoryGrid, SpreadsheetEngine, WorkbookAdapter, MemoryDataSource


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


class _SectionCard(QFrame):
    def __init__(self, doc: dict, doc_service: DocumentService, on_edit, on_delete):
        super().__init__()
        self._doc = doc
        self._doc_service = doc_service
        self._on_edit = on_edit
        self._on_delete = on_delete

        self.setStyleSheet(f"""
            _SectionCard {{
                background: {COLOR_SURFACE};
                border: 1px solid {COLOR_BORDER};
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 12, 16, 12)
        lay.setSpacing(8)

        # Row 1: icon + name + type badge
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        icon = doc.get("icon", "\U0001f4c4")
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 22px;")
        row1.addWidget(icon_lbl)

        name_lbl = QLabel(doc["name"])
        name_lbl.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {COLOR_TEXT};")
        row1.addWidget(name_lbl)

        cat_name = doc.get("category_name", "")
        if cat_name:
            badge = QLabel(cat_name)
            badge.setStyleSheet(f"""
                background: {COLOR_ACCENT}22; color: {COLOR_ACCENT};
                font-size: 10px; padding: 2px 8px; font-weight: 600;
            """)
            row1.addWidget(badge)

        row1.addStretch()

        updated = doc.get("updated_at", "")
        if updated:
            date_lbl = QLabel(f"Editado: {updated}")
            date_lbl.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 11px;")
            row1.addWidget(date_lbl)

        lay.addLayout(row1)

        # Row 2: description (if any)
        desc = doc.get("description", "")
        if desc:
            desc_lbl = QLabel(desc)
            desc_lbl.setWordWrap(True)
            desc_lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
            lay.addWidget(desc_lbl)

        # Row 3: mini preview
        self._preview_container = QVBoxLayout()
        self._preview_container.setSpacing(0)
        lay.addLayout(self._preview_container)
        self._load_preview()

        # Row 4: actions
        row4 = QHBoxLayout()
        row4.setSpacing(8)

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
        row4.addWidget(edit_btn)

        delete_btn = QPushButton("Eliminar")
        delete_btn.setCursor(Qt.PointingHandCursor)
        delete_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {COLOR_DANGER};
                border: 1px solid {COLOR_DANGER};
                padding: 4px 16px; font-size: 12px;
            }}
            QPushButton:hover {{ background: {COLOR_DANGER}15; }}
        """)
        delete_btn.clicked.connect(lambda: self._on_delete(self._doc["id"]))
        row4.addWidget(delete_btn)

        row4.addStretch()
        lay.addLayout(row4)

    def _load_preview(self):
        doc_id = self._doc["id"]
        wb_json = self._doc_service.latest_workbook(doc_id)
        if not wb_json:
            empty = QLabel("(vacío)")
            empty.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 11px; padding: 4px 0;")
            self._preview_container.addWidget(empty)
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
                self._preview_container.addWidget(empty)
                return

            source = MemoryDataSource(rows, cols)
            engine = SpreadsheetEngine(grid, source)
            from widgets.workbook_renderer import EngineSheetModel

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
            self._preview_container.addWidget(tv)
        except Exception:
            err = QLabel("Error al cargar vista previa")
            err.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
            self._preview_container.addWidget(err)

    def refresh_preview(self):
        for i in range(self._preview_container.count()):
            w = self._preview_container.itemAt(i).widget()
            if w:
                w.deleteLater()
        self._load_preview()


class DocumentManagerView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._doc_service: DocumentService = ServiceRegistry.instance().spreadsheet().doc_service
        self._categories: list = []
        self._documents: list = []
        self._cards: list[_SectionCard] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._build_header()
        layout.addWidget(self._header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self._container = QWidget()
        self._container.setStyleSheet("background: transparent;")
        self._list_layout = QVBoxLayout(self._container)
        self._list_layout.setContentsMargins(24, 16, 24, 16)
        self._list_layout.setSpacing(12)
        self._list_layout.addStretch()

        scroll.setWidget(self._container)
        layout.addWidget(scroll, 1)

        self._load_categories()
        self.refresh()

    def _build_header(self):
        self._header = QFrame()
        self._header.setStyleSheet(f"background: {COLOR_SURFACE}; border-bottom: 1px solid {COLOR_BORDER};")
        hl = QHBoxLayout(self._header)
        hl.setContentsMargins(24, 16, 24, 12)

        vl = QVBoxLayout()
        vl.setSpacing(2)
        title = QLabel("Meta Editor")
        title.setStyleSheet(f"font-size: 20px; font-weight: 700; color: {COLOR_TEXT};")
        vl.addWidget(title)
        subtitle = QLabel("Secciones de la aplicación — Diseñador de plantillas")
        subtitle.setStyleSheet(f"font-size: 12px; color: {COLOR_TEXT_DIM};")
        vl.addWidget(subtitle)
        hl.addLayout(vl)

        hl.addStretch()

        self._search = QLineEdit()
        self._search.setPlaceholderText("Buscar sección...")
        self._search.setFixedWidth(200)
        self._search.setStyleSheet(f"""
            QLineEdit {{
                background: {COLOR_INPUT}; color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER};
                padding: 5px 10px; font-size: 13px;
            }}
        """)
        self._search.textChanged.connect(self._filter)
        hl.addWidget(self._search)

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

    def _filter(self):
        text = self._search.text().strip().lower()
        for card in self._cards:
            name = card._doc.get("name", "").lower()
            card.setVisible(not text or text in name)

    def _load_categories(self):
        self._categories = self._doc_service.get_categories()

    def refresh(self):
        self._load_categories()
        self._rebuild_list()

    def _rebuild_list(self):
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()

        self._documents = self._doc_service.list_documents()
        for doc in self._documents:
            card = _SectionCard(doc, self._doc_service, self._edit_section, self._delete_section)
            self._cards.append(card)
            self._list_layout.addWidget(card)
        if not self._documents:
            empty = QLabel("No hay secciones. Crea la primera con «+ Nueva sección».")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 14px; padding: 40px;")
            self._list_layout.addWidget(empty)
        self._list_layout.addStretch()

    def _edit_section(self, doc_id: int):
        doc = next((d for d in self._documents if d["id"] == doc_id), None)
        if not doc:
            return
        self._doc_service.open(doc_id)
        editor = getattr(self.main, "_editor_instance", None)
        if editor:
            self._doc_service.load_into_editor(editor, doc_id)
            editor._toggle_fullscreen()

    def _delete_section(self, doc_id: int):
        doc = next((d for d in self._documents if d["id"] == doc_id), None)
        if not doc:
            return
        reply = QMessageBox.question(
            self, "Eliminar sección",
            f"¿Desea eliminar la sección «{doc['name']}»?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self._doc_service.delete(doc_id)
        self.refresh()

    def _new_section(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Nueva sección")
        dlg.setMinimumWidth(400)
        dlg.setStyleSheet(f"background: {COLOR_SURFACE}; color: {COLOR_TEXT};")

        form = QFormLayout(dlg)
        form.setSpacing(10)
        form.setContentsMargins(20, 16, 20, 16)

        name_input = QLineEdit()
        name_input.setPlaceholderText("Ej: Notas Matemáticas")
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
        btns.button(QDialogButtonBox.Ok).setStyleSheet(f"""
            QPushButton {{
                background: {COLOR_ACCENT}; color: #fff;
                border: none; padding: 6px 16px; font-weight: 600;
            }}
        """)
        btns.button(QDialogButtonBox.Cancel).setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {COLOR_TEXT};
                border: 1px solid {COLOR_BORDER}; padding: 6px 16px;
            }}
        """)
        form.addRow(btns)

        if dlg.exec() != QDialog.Accepted:
            return

        name = name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "El nombre es obligatorio.")
            return

        cat_id = type_combo.currentData()
        desc = desc_input.toPlainText().strip()

        doc_id = self._doc_service.create(
            name=name, category_id=cat_id, description=desc,
        )
        if doc_id:
            self.refresh()
            self._edit_section(doc_id)
