from __future__ import annotations
import json
from typing import Any, Dict, List, Optional

from spreadsheet.services import DocumentService
from spreadsheet.adapters import WorkbookAdapter


class SpreadsheetService:
    def __init__(self):
        self._doc_service = DocumentService()
        self._adapter = WorkbookAdapter()

    @property
    def doc_service(self) -> DocumentService:
        return self._doc_service

    def open(self, section_key: str) -> bool:
        return self._doc_service.open(section_key)

    def save(self) -> bool:
        return self._doc_service.save()

    def close(self) -> None:
        self._doc_service.close()

    def load_into_editor(self, editor_view) -> None:
        self._doc_service.load_into_editor(editor_view)

    def save_from_editor(self, editor_view) -> None:
        self._doc_service.save_from_editor(editor_view)

    def summary(self) -> dict:
        return self._doc_service.summary()
