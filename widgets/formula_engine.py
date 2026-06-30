from __future__ import annotations
import json, os
from typing import Any, Dict, List, Optional, Callable

from PySide6.QtCore import QObject, Qt, QUrl, Signal
from PySide6.QtWidgets import QWidget

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    try:
        from PyQt5.QtWebEngineWidgets import QWebEngineView
    except ImportError:
        QWebEngineView = None

ASSETS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "assets", "luckysheet"
)


class PendingCall:
    def __init__(self, js: str, callback: Optional[Callable] = None):
        self.js = js
        self.callback = callback


class FormulaEngine(QObject):
    """
    Singleton: mantiene un QWebEngineView oculto con Luckysheet en modo headless.

    Es el único motor de cálculo de fórmulas de EduSuite.
    La UI nunca ve este QWebEngineView.
    """

    cellsChanged = Signal(int, list)

    _instance: Optional["FormulaEngine"] = None

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._ready = False
        self._view: Optional[QWebEngineView] = None
        self._pending: List[PendingCall] = []
        self._current_workbook: Optional[str] = None
        self._init_view()

    @classmethod
    def instance(cls) -> "FormulaEngine":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _init_view(self) -> None:
        if QWebEngineView is None:
            return
        self._view = QWebEngineView()
        self._view.setFixedSize(0, 0)
        self._view.hide()
        self._view.page().setBackgroundColor(Qt.transparent)
        html_path = os.path.join(ASSETS_DIR, "standalone.html")
        self._view.load(QUrl.fromLocalFile(html_path + "?mode=headless"))
        self._view.loadFinished.connect(self._on_loaded)

    def _on_loaded(self, ok: bool) -> None:
        if not ok:
            return
        self._ready = True
        for item in self._pending:
            self._view.page().runJavaScript(item.js, item.callback)
        self._pending.clear()
        if self._current_workbook is not None:
            self._load_workbook_internal(self._current_workbook)

    def _run_js(self, js: str, callback: Optional[Callable] = None) -> None:
        if self._ready and self._view is not None:
            self._view.page().runJavaScript(js, callback)
        else:
            self._pending.append(PendingCall(js, callback))

    def _load_workbook_internal(self, workbook_json: str) -> None:
        js = f"window.__engineLoadWorkbook({workbook_json})"
        self._run_js(js)

    def load_workbook(self, workbook_json: str) -> None:
        self._current_workbook = workbook_json
        if self._ready:
            self._load_workbook_internal(workbook_json)

    def set_cell(self, sheet: int, row: int, col: int, value: Any) -> None:
        msg = json.dumps({
            "type": "setCell",
            "sheet": sheet,
            "row": row,
            "col": col,
            "value": value
        })
        js = f"window.__engineHandleMessage({msg})"
        self._run_js(js, self._on_set_cell_result)

    def _on_set_cell_result(self, result: Any) -> None:
        if result is None:
            return
        try:
            data = json.loads(result) if isinstance(result, str) else result
            if isinstance(data, dict) and data.get("type") == "changed":
                sheet = data.get("sheet", 0)
                self.cellsChanged.emit(int(sheet), data.get("cells", []))
        except (json.JSONDecodeError, TypeError):
            pass

    def get_workbook(self, callback: Callable) -> None:
        js = "JSON.stringify({type:'workbook', data:(function(){var fs=luckysheet.getluckysheetfile();return Array.isArray(fs)?fs.map(function(f){return {name:f.name,celldata:f.celldata||[],config:f.config||{}}}):[];})()})"
        self._run_js(js, lambda r: callback(r) if callback else None)

    def shutdown(self) -> None:
        if self._view is not None:
            self._view.page().deleteLater()
            self._view.deleteLater()
            self._view = None
        self._ready = False
        self._pending.clear()
