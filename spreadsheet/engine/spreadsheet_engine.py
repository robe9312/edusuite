from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from ..core.grid import Grid
from ..core.grid_cell import GridCell
from ..core.grid_range import GridRange
from ..core.grid_metadata import GridMetadata
from ..core.events import EventBus, GridEvent, CellEvent
from ..datasource.base import DataSource
from ..cache.block_cache import BlockCache
from ..commands.undo_engine import UndoEngine
from ..commands.command import SetCellCommand, CellChange
from ..commands.selection import SelectionEngine
from ..commands.clipboard import Clipboard, ClipboardData, ClipboardFormat


class SpreadsheetEngine:
    def __init__(self, grid: Grid, source: DataSource):
        self.grid = grid
        self.source = source
        self.cache = BlockCache(source)
        self.undo = UndoEngine()
        self.selection = SelectionEngine()
        self.clipboard = Clipboard()
        self.events = EventBus()

    def get_cell(self, row: int, col: int) -> GridCell:
        cached = self.cache.get(row, col)
        if cached is not None:
            return cached
        return self.grid.cell(row, col)

    def set_cell(self, row: int, col: int, cell: GridCell) -> None:
        old = self.get_cell(row, col)
        self.cache.set(row, col, cell)
        self.grid.set_cell(row, col, cell)
        event = CellEvent(row=row, col=col, old_value=old, new_value=cell)
        self.events.emit("cell_changed", event)

    def edit_cell(self, row: int, col: int, value: Any) -> None:
        old = self.get_cell(row, col)
        new = GridCell(value=value, display=str(value))
        cmd = SetCellCommand(self.grid, [
            CellChange(row, col, old, new)
        ])
        self.undo.execute(cmd)
        self.cache.set(row, col, new)
        event = CellEvent(row=row, col=col, old_value=old, new_value=new)
        self.events.emit("cell_changed", event)

    def get_range(self, r: GridRange) -> List[List[GridCell]]:
        return self.grid.range(r)

    def set_range(self, r: GridRange, data: List[List[GridCell]]) -> None:
        changes = []
        for dr, row_data in enumerate(data):
            for dc, cell in enumerate(row_data):
                rr, cc = r.row_start + dr, r.col_start + dc
                old = self.get_cell(rr, cc)
                changes.append(CellChange(rr, cc, old, cell))
                self.cache.set(rr, cc, cell)
        cmd = SetCellCommand(self.grid, changes)
        self.undo.execute(cmd)

    def copy_selection(self) -> None:
        r = self.selection.state.current
        if not r:
            return
        data = self.get_range(r)
        self.clipboard.copy(ClipboardData(
            format=ClipboardFormat.GRID_CELLS,
            data=data,
            source_range=(r.row_start, r.col_start, r.row_end, r.col_end),
        ))

    def paste(self, row: int, col: int) -> None:
        cb = self.clipboard.paste()
        if not cb or cb.format != ClipboardFormat.GRID_CELLS:
            return
        data: List[List[GridCell]] = cb.data
        h = len(data)
        w = len(data[0]) if data else 0
        target = GridRange(row, col, row + h - 1, col + w - 1)
        self.set_range(target, data)

    def row_count(self) -> int:
        return max(self.grid.row_count(), self.source.row_count())

    def col_count(self) -> int:
        return max(self.grid.col_count(), self.source.col_count())

    def flush(self) -> None:
        self.cache.flush()

    def load_from_luckysheet(self, sheets: List[dict], index: int = 0) -> None:
        from ..datasource.workbook_source import WorkbookDataSource
        ws = WorkbookDataSource(sheets, index)
        ws.connect()
        self.source = ws
        self.cache = BlockCache(ws)
        self.cache.flush()

    def to_luckysheet_data(self) -> List[dict]:
        rows = self.row_count()
        cols = self.col_count()
        celldata = []
        for r in range(rows):
            for c in range(cols):
                cell = self.get_cell(r, c)
                if cell.data_type.value != "blank" or cell.value is not None:
                    celldata.append({
                        "r": r, "c": c,
                        "v": {"v": cell.value, "m": cell.display}
                    })
        return [{"celldata": celldata, "row": rows, "column": cols}]
