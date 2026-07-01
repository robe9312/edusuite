import json
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, QTimer, Signal
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
from spreadsheet.renderer import WorkbookRenderer, SpreadsheetModel
from .formula_engine import FormulaEngine


class WorkbookRenderView(QWidget):
    edit_requested = Signal(str)
    delete_requested = Signal(str)

    def __init__(self, section, doc_service=None, parent=None):
        super().__init__(parent)
        # Asegurar que section sea un diccionario
        if isinstance(section, int):
            from db.database import get_custom_section
            section = get_custom_section(section) or {}
        self.section = section
        self._doc_service = doc_service or DocumentService()
        self._content_widget = None
        self._sheet_renderers: list = []
        self._tables: list = []
        self._engine: Optional[FormulaEngine] = None
        self._wb_cache: List[Dict[str, Any]] = []

        self._auto_timer = QTimer(self)
        self._auto_timer.setSingleShot(True)
        self._auto_timer.timeout.connect(self._do_auto_save)

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

        # Parse local cache — cada vista tiene el suyo, el engine singleton nunca se lee para persistir
        try:
            parsed = json.loads(workbook_json) if isinstance(workbook_json, str) else workbook_json or []
            if isinstance(parsed, dict) and "sheetData" in parsed:
                parsed = parsed["sheetData"] or []
            self._wb_cache = json.loads(json.dumps(parsed if isinstance(parsed, list) else []))
        except (json.JSONDecodeError, TypeError, ValueError):
            self._wb_cache = []

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
                        background: {COLOR_SURFACE};
                        border: 1px solid {COLOR_BORDER};
                        gridline-color: {COLOR_BORDER}55;
                        color: {COLOR_TEXT};
                        font-size: 12px;
                        outline: none;
                    }}
                    QTableView::item {{
                        padding: 4px 10px;
                        border: none;
                    }}
                    QTableView::item:hover {{
                        background: {COLOR_ACCENT}18;
                    }}
                    QTableView::item:selected {{
                        background: {COLOR_ACCENT}22;
                        border: 1px solid {COLOR_ACCENT}88;
                        color: {COLOR_TEXT};
                    }}
                    QHeaderView::section {{
                        background: {COLOR_PANEL};
                        color: {COLOR_TEXT_MUTED};
                        font-weight: 600;
                        padding: 6px 8px;
                        border: none;
                        border-bottom: 1px solid {COLOR_BORDER};
                        font-size: 11px;
                    }}
                """)
                model = page.model()
                if isinstance(model, SpreadsheetModel):
                    model.cellEdited.connect(self._on_cell_edited)
                self._tables.append(page)
        self._content_widget = container
        self._body_layout.addWidget(container)

        if self._engine is not None:
            try:
                self._engine.cellsChanged.disconnect()
            except (TypeError, RuntimeError):
                pass
            self._engine.cellsChanged.connect(self._on_engine_changed)

    def _on_cell_edited(self, row: int, col: int, value: object) -> None:
        if self._engine is None:
            return
        model = self.sender()
        if not isinstance(model, SpreadsheetModel):
            return
        self._engine.set_cell(model.sheet_index, row, col, str(value) if value is not None else "")

    def _on_engine_changed(self, sheet_index: int, cells: list) -> None:
        if not cells:
            return
        if sheet_index < len(self._tables):
            table = self._tables[sheet_index]
            model = table.model()
            if isinstance(model, SpreadsheetModel):
                model.update_cells(cells)
         # Apply diff to local cache (cada vista tiene el suyo, el engine singleton es compartido)
        print(f"🔄 WorkbookRenderer: Engine changed - sheet={sheet_index}, celdas={len(cells)}")
        self._apply_diff_to_cache(sheet_index, cells)
        print("⏳ WorkbookRenderer: Auto-save timer iniciado")
        self._auto_timer.start(2000)

    def _apply_diff_to_cache(self, sheet_idx: int, cells: list) -> None:
        if sheet_idx >= len(self._wb_cache):
            return
        sheet = self._wb_cache[sheet_idx]
        celldata = sheet.get("celldata")
        if not isinstance(celldata, list):
            celldata = []
            sheet["celldata"] = celldata
        idx: Dict[Tuple[int, int], int] = {}
        for i, c in enumerate(celldata):
            rr = c.get("r")
            cc = c.get("c")
            if rr is not None and cc is not None:
                idx[(rr, cc)] = i
        for cell in cells:
            r = cell.get("r")
            c = cell.get("c")
            v = cell.get("v")
            if r is None or c is None:
                continue
            key = (r, c)
            if v is None:
                if key in idx:
                    celldata.pop(idx[key])
                    idx.clear()
                    for i2, c2 in enumerate(celldata):
                        rr2 = c2.get("r")
                        cc2 = c2.get("c")
                        if rr2 is not None and cc2 is not None:
                            idx[(rr2, cc2)] = i2
            else:
                if not isinstance(v, dict):
                    v = {"v": v, "m": str(v)}
                if key in idx:
                    celldata[idx[key]]["v"] = v
                else:
                    idx[key] = len(celldata)
                    celldata.append({"r": r, "c": c, "v": v})

    def _do_auto_save(self) -> None:
        if not self._wb_cache:
            return
        print(f"💾 WorkbookRenderer: Auto-save ejecutado para sección {self.section.get('name')} (ID: {self.section.get('id')})")
        try:
            cache_copy = json.loads(json.dumps(self._wb_cache))
            for sheet in cache_copy:
                if not isinstance(sheet, dict):
                    continue
                max_r, max_c = self._calc_area(sheet)
                meta = sheet.get("metadata") or {}
                meta["active_area"] = {"top": 0, "left": 0, "bottom": max_r, "right": max_c}
                sheet["metadata"] = meta
            updated = json.dumps(cache_copy)
            print(f"📝 WorkbookRenderer: JSON a guardar (truncado): {updated[:200]}...")
        except (json.JSONDecodeError, TypeError, ValueError) as e:
            print(f"❌ WorkbookRenderer: Error en auto-save - {e}")
            log_msg(f"AUTO_SAVE_ERROR {e}")
            return
        section_id = self.section.get("id")
        doc_id = self.section.get("document_id")
        print(f"🆔 WorkbookRenderer: Section ID={section_id}, Doc ID={doc_id}")
        if section_id:
            from db.database import update_section_workbook
            update_section_workbook(section_id, updated)
            print("✅ WorkbookRenderer: Sección actualizada en DB")
        if doc_id:
            from db.database import save_document_version
            save_document_version(doc_id, updated, comment="Auto-guardado")
            print("✅ WorkbookRenderer: Versión de documento guardada en DB")
        log_msg(f"AUTO_SAVE section={self.section.get('name')} len={len(updated)}")

    @staticmethod
    def _calc_area(sheet: Dict[str, Any]) -> Tuple[int, int]:
        max_r = -1
        max_c = -1
        for key in ("celldata", "data"):
            raw = sheet.get(key)
            if key == "celldata" and isinstance(raw, list):
                for cell in raw:
                    r = cell.get("r")
                    c = cell.get("c")
                    if r is not None and r > max_r: max_r = r
                    if c is not None and c > max_c: max_c = c
            elif key == "data" and isinstance(raw, list):
                for r, row in enumerate(raw):
                    if not isinstance(row, list):
                        continue
                    for c, cell in enumerate(row):
                        if cell is not None:
                            if r > max_r: max_r = r
                            if c > max_c: max_c = c
        cfg = sheet.get("config") or {}
        for key in ("rowlen", "columnlen"):
            raw = cfg.get(key) or {}
            if isinstance(raw, dict):
                for k in raw:
                    if str(k).isdigit():
                        i = int(k)
                        if key == "rowlen" and i > max_r: max_r = i
                        if key == "columnlen" and i > max_c: max_c = i
        for merge_key in ("merge", "merges", "Merge"):
            raw = cfg.get(merge_key)
            if isinstance(raw, dict):
                items = raw.values()
            elif isinstance(raw, list):
                items = raw
            else:
                continue
            for span in items:
                if not isinstance(span, dict):
                    continue
                er = span.get("r", 0) + span.get("rs", 1) - 1
                ec = span.get("c", 0) + span.get("cs", 1) - 1
                if er > max_r: max_r = er
                if ec > max_c: max_c = ec
        if max_r < 0: max_r = 4
        if max_c < 0: max_c = 3
        return max_r, max_c

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
