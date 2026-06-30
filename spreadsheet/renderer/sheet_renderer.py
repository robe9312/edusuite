from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHeaderView, QTableView,
)

from .render_context import RenderContext
from .layout_renderer import LayoutRenderer
from .style_renderer import StyleRenderer
from .merge_renderer import MergeRenderer
from .spreadsheet_model import SpreadsheetModel


class SheetRenderer:
    """
    Renderiza UNA hoja del workbook en un `QTableView`+`SpreadsheetModel`.

    Pipeline (NO hace otra cosa):
      Sheet JSON
        → Layout (área activa, tamaños)
        → Model (SpreadsheetModel, estilo vía roles Qt)
        → Merge (setSpan)
        → QTableView

    No sabe de la aplicación ni del dominio.
    """

    def __init__(self, context: RenderContext):
        self.ctx = context
        self._normalize_sheet()
        self.layout = LayoutRenderer(context)
        self.styles = StyleRenderer()
        self.merges = MergeRenderer(context.sheet_data)
        self.celldata_index = self._index_celldata(context.sheet_data)
        self.model: Optional[SpreadsheetModel] = None

    def _normalize_sheet(self) -> None:
        sheet = self.ctx.sheet_data or {}
        celldata = sheet.get("celldata")
        if isinstance(celldata, list) and len(celldata) > 0:
            return
        data = sheet.get("data")
        if isinstance(data, list) and len(data) > 0:
            flat = []
            for r, row in enumerate(data):
                if not isinstance(row, list):
                    continue
                for c, cell in enumerate(row):
                    if cell is not None:
                        v = cell if isinstance(cell, dict) else {"v": cell, "m": str(cell)}
                        flat.append({"r": r, "c": c, "v": v})
            if flat:
                sheet["celldata"] = flat

    def render(self, parent=None) -> QTableView:
        self.layout.compute()
        rows = self.ctx.rows()
        cols = self.ctx.cols()

        self.model = SpreadsheetModel(
            rows=rows,
            cols=cols,
            celldata_index=self.celldata_index,
            styles=self.styles,
            sheet_index=self.ctx.sheet_index,
            parent=parent,
        )

        table = QTableView(parent)
        table.setModel(self.model)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setDefaultSectionSize(
            self.layout.DEFAULT_COL_WIDTH
        )
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        for c in range(cols):
            width = self.layout.column_width(c)
            table.setColumnWidth(c, width)

        for r in range(rows):
            height = self.layout.row_height(r)
            table.setRowHeight(r, height)

        for span in self.merges.spans():
            r, c, rs, cs = span["r"], span["c"], span["rs"], span["cs"]
            if r < rows and c < cols:
                try:
                    table.setSpan(r, c, rs, cs)
                except Exception:
                    pass

        return table

    def update_cells(self, table: QTableView, changed: List[Dict[str, Any]]) -> None:
        if not changed or self.model is None:
            return
        self.model.update_cells(changed)

    @staticmethod
    def _index_celldata(sheet: Dict[str, Any]) -> Dict[Tuple[int, int], Dict[str, Any]]:
        idx: Dict[Tuple[int, int], Dict[str, Any]] = {}
        celldata = (sheet or {}).get("celldata") or []
        for cell in celldata:
            r = cell.get("r")
            c = cell.get("c")
            v = cell.get("v")
            if r is None or c is None:
                continue
            if isinstance(v, dict):
                idx[(r, c)] = v
            elif v is not None:
                idx[(r, c)] = {"v": v}
        return idx
