from __future__ import annotations
import json
from typing import Any, Dict, List, Optional

from ..core.memory_grid import MemoryGrid
from ..core.grid import Grid
from ..engine.spreadsheet_engine import SpreadsheetEngine
from ..adapters.workbook_adapter import WorkbookAdapter
from ..datasource.memory_source import MemoryDataSource


class DocumentService:
    def __init__(self):
        self._adapter = WorkbookAdapter()
        self._engine: Optional[SpreadsheetEngine] = None
        self._current_id: Optional[int] = None
        self._current_meta: dict = {}

    def open(self, doc_id: int) -> bool:
        from db.database import get_document, get_latest_workbook
        from logs.logger import log as log_msg
        doc = get_document(doc_id)
        if not doc:
            log_msg(f"DOC_OPEN doc_id={doc_id} NOT_FOUND")
            return False

        self._current_id = doc["id"]
        self._current_meta = dict(doc)

        wb_row = get_latest_workbook(doc_id)
        has_wb = bool(wb_row and wb_row.get("workbook_json"))
        log_msg(f"DOC_OPEN doc_id={doc_id} name={doc.get('name')} has_workbook={has_wb}")
        wb_data = (wb_row.get("workbook_json") or "[]") if wb_row else "[]"
        if isinstance(wb_data, str):
            wb_data = json.loads(wb_data)

        if wb_data:
            self._adapter.load(wb_data)
        else:
            self._adapter.load([])
            if self._adapter.sheet_count() == 0:
                self._adapter.add_sheet(doc.get("name", "Sheet 1"))

        grid = self._adapter.sheet(0)
        if grid is None:
            log_msg(f"DOC_OPEN doc_id={doc_id} NO_SHEET")
            return False

        source = MemoryDataSource(grid.row_count(), grid.col_count())
        self._engine = SpreadsheetEngine(grid, source)
        log_msg(f"DOC_OPEN doc_id={doc_id} OK grid={grid.row_count()}x{grid.col_count()}")
        return True

    def create(self, name: str, category_id: int = 6, description: str = "",
               icon: str = "\U0001f4c4", color: str = "#5e81f4",
               school_year: str = "") -> Optional[int]:
        from db.database import create_document
        try:
            doc_id = create_document(
                name=name, category_id=category_id,
                description=description, icon=icon, color=color,
                school_year=school_year,
            )
        except Exception:
            return None

        self._adapter = WorkbookAdapter()
        self._adapter.add_sheet(name or "Sheet 1")
        self._adapter.name = name

        grid = self._adapter.sheet(0)
        source = MemoryDataSource()
        self._engine = SpreadsheetEngine(grid, source)
        self._current_id = doc_id
        self._current_meta = {
            "id": doc_id, "name": name, "category_id": category_id,
            "icon": icon, "color": color,
        }
        self.save("Creado")
        return doc_id

    def save(self, comment: str = "") -> bool:
        if not self._engine or not self._current_id:
            return False
        from db.database import save_document_version
        data = self._adapter.save()
        wb_json = json.dumps(data, ensure_ascii=False)
        save_document_version(self._current_id, wb_json, comment=comment)
        self._engine.flush()
        return True

    def close(self) -> None:
        if self._engine and self._engine.grid.dirty:
            self.save()
        self._engine = None
        self._adapter = WorkbookAdapter()
        self._current_id = None
        self._current_meta = {}

    def duplicate(self, doc_id: int, new_name: Optional[str] = None) -> Optional[int]:
        from db.database import duplicate_document
        return duplicate_document(doc_id, new_name)

    def archive(self, doc_id: int) -> None:
        from db.database import archive_document
        archive_document(doc_id)

    def restore(self, doc_id: int) -> None:
        from db.database import restore_document
        restore_document(doc_id)

    def delete(self, doc_id: int) -> None:
        from db.database import delete_document
        delete_document(doc_id)

    def history(self, doc_id: int) -> List[dict]:
        from db.database import get_document_versions
        return get_document_versions(doc_id)

    def rollback(self, doc_id: int, version_id: int) -> bool:
        from db.database import get_document_version, save_document_version
        ver = get_document_version(version_id)
        if not ver or not ver.get("workbook_json"):
            return False
        save_document_version(doc_id, ver["workbook_json"],
                              comment=f"Rollback a versión {ver['version']}")
        return True

    def preview(self, doc_id: int) -> Optional[SpreadsheetEngine]:
        self.open(doc_id)
        return self._engine

    def export_json(self, doc_id: int) -> Optional[list]:
        from db.database import get_latest_workbook
        wb = get_latest_workbook(doc_id)
        if wb and wb.get("workbook_json"):
            return json.loads(wb["workbook_json"]) if isinstance(wb["workbook_json"], str) else wb["workbook_json"]
        return None

    def list_documents(self, category_id: Optional[int] = None,
                       school_year: Optional[str] = None,
                       archived: bool = False,
                       search: Optional[str] = None) -> List[dict]:
        from db.database import get_all_documents
        return get_all_documents(category_id, school_year, archived, search)

    def get_categories(self) -> List[dict]:
        from db.database import get_document_categories
        return get_document_categories()

    def latest_workbook(self, doc_id: int) -> Optional[str]:
        from db.database import get_latest_workbook
        wb = get_latest_workbook(doc_id)
        if wb:
            return wb.get("workbook_json")
        return None

    @property
    def engine(self) -> Optional[SpreadsheetEngine]:
        return self._engine

    @property
    def adapter(self) -> WorkbookAdapter:
        return self._adapter

    @property
    def current_id(self) -> Optional[int]:
        return self._current_id

    @property
    def meta(self) -> dict:
        return dict(self._current_meta)

    def undo(self) -> bool:
        if self._engine:
            return self._engine.undo.undo()
        return False

    def redo(self) -> bool:
        if self._engine:
            return self._engine.undo.redo()
        return False

    def can_undo(self) -> bool:
        return self._engine is not None and self._engine.undo.can_undo()

    def can_redo(self) -> bool:
        return self._engine is not None and self._engine.undo.can_redo()

    def load_luckysheet(self, sheets: List[dict]) -> None:
        self._adapter.load(sheets)
        grid = self._adapter.sheet(0)
        if grid is None:
            return
        source = MemoryDataSource(grid.row_count(), grid.col_count())
        self._engine = SpreadsheetEngine(grid, source)

    def to_luckysheet(self) -> List[dict]:
        return self._adapter.save()

    def load_into_editor(self, editor_view, doc_id=None) -> None:
        if not editor_view:
            return
        ls_data = self._adapter.save() if self._engine else []
        meta = self._current_meta
        payload = {
            "sheetData": ls_data,
            "name": meta.get("name", "Documento"),
        }
        editor_view.load_workbook(payload, doc_id or self._current_id)

    def save_workbook(self, doc_id: int, workbook_json: str) -> bool:
        from db.database import save_document_version
        try:
            save_document_version(doc_id, workbook_json, comment="Auto-guardado")
            return True
        except Exception:
            return False

    def save_version(self, doc_id: int, workbook_json: str, comment: str = "") -> bool:
        from db.database import save_document_version
        try:
            save_document_version(doc_id, workbook_json, comment=comment)
            return True
        except Exception:
            return False

    def save_from_editor(self, editor_view) -> bool:
        if not editor_view or not self._current_id:
            return False
        editor_view._save_from_editor()
        return True
