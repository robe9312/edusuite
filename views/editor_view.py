import os, json, uuid, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from logs.logger import log as log_msg

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QFrame, QSizePolicy,
)
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    try:
        from PyQt5.QtWebEngineWidgets import QWebEngineView
    except ImportError:
        QWebEngineView = None

from config import *

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "luckysheet")
DATA_FILE = "/tmp/edusuite_workbook.json"
SAVE_FILE = "/tmp/edusuite_save.json"
SECTION_ID_FILE = "/tmp/edusuite_section_id.txt"


def _write_workbook_data(workbook_json, name="Sección", section_id=None):
    import json
    data = json.loads(workbook_json) if isinstance(workbook_json, str) else workbook_json
    if isinstance(data, list):
        payload = {"sheetData": data, "name": name}
    else:
        payload = {"sheetData": [], "name": name}
    with open(DATA_FILE, "w") as f:
        json.dump(payload, f)
    if section_id is not None:
        with open(SECTION_ID_FILE, "w") as f:
            f.write(str(section_id))
    else:
        try:
            os.remove(SECTION_ID_FILE)
        except FileNotFoundError:
            pass
    try:
        os.remove(SAVE_FILE)
    except FileNotFoundError:
        pass


def _extract_sheet_data(sheet):
    """Extract (headers, rows) from a LuckySheet sheet object.
    Handles both celldata (flat {r,c,v}) and data (2D array) formats.
    """
    grid = {}
    max_r = max_c = 0

    celldata = sheet.get("celldata")
    if isinstance(celldata, list) and len(celldata) > 0:
        for cell in celldata:
            r, c = cell["r"], cell["c"]
            v = cell.get("v", {})
            grid[(r, c)] = v
            if r > max_r: max_r = r
            if c > max_c: max_c = c
    else:
        data = sheet.get("data")
        if isinstance(data, list) and len(data) > 0:
            for r, row in enumerate(data):
                if not isinstance(row, list):
                    continue
                for c, cell in enumerate(row):
                    if cell is not None:
                        grid[(r, c)] = cell if isinstance(cell, dict) else {"v": cell, "m": str(cell)}
                        if r > max_r: max_r = r
                        if c > max_c: max_c = c

    if not grid:
        return [], []

    headers = []
    for c in range(max_c + 1):
        cell = grid.get((0, c))
        if cell is not None:
            val = cell.get("m", cell.get("v", ""))
            headers.append(str(val) if val is not None else "")
        else:
            headers.append("")

    while headers and headers[-1] == "":
        headers.pop()
    if not headers:
        return [], []

    rows = []
    for r in range(1, max_r + 1):
        row_data = {}
        has_data = False
        for j, h in enumerate(headers):
            cell = grid.get((r, j))
            if cell is not None:
                v = cell.get("v")
                m = cell.get("m", "")
                val = m if m else (str(v) if v is not None else "")
                row_data[h] = val
                if val:
                    has_data = True
            else:
                row_data[h] = ""
        if has_data:
            rows.append(row_data)

    return headers, rows


class _Handler(BaseHTTPRequestHandler):
    engine = None
    section_id = None
    _save_timer = None

    def do_GET(self):
        if self.path == "/data":
            try:
                with open(DATA_FILE, "r") as f:
                    raw = f.read()
                data = json.loads(raw)
                if not isinstance(data, dict):
                    data = {}
            except (FileNotFoundError, json.JSONDecodeError):
                data = {}
            if "sheetData" not in data:
                data["sheetData"] = []
            if "name" not in data:
                data["name"] = "Editor"
            self._send_json(json.dumps(data))
        elif self.path.startswith("/load_template"):
            from urllib.parse import urlparse, parse_qs
            qs = parse_qs(urlparse(self.path).query)
            tid = qs.get("id", [None])[0]
            if tid and self.engine:
                ver = self.engine.get_latest_version(int(tid))
                self._send_json(ver["json_blob"] if ver else "{}")
            else:
                self._send_json("{}")
        elif self.path == "/templates":
            if self.engine:
                projects = self.engine.list_projects(active_only=False)
                out = json.dumps([{"id": p["id"], "name": p["name"]} for p in projects])
            else:
                out = "[]"
            self._send_json(out)
        elif self.path == "/sections":
            from db.database import get_all_custom_sections
            secs = get_all_custom_sections()
            out = json.dumps([{"id": s["id"], "key": s["section_key"], "name": s["name"], "icon": s.get("icon", "📄"), "columns_count": len(__import__("json").loads(s.get("columns_json", "[]")))} for s in secs])
            self._send_json(out)
        elif self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            html_path = os.path.join(ASSETS_DIR, "standalone.html")
            with open(html_path, "r") as f:
                self.wfile.write(f.read().encode("utf-8"))
        else:
            static_path = os.path.join(ASSETS_DIR, self.path.lstrip("/"))
            if os.path.isfile(static_path):
                ext = os.path.splitext(static_path)[1]
                ct = {"css": "text/css", "js": "application/javascript", "png": "image/png",
                      "svg": "image/svg+xml", "woff": "font/woff", "woff2": "font/woff2",
                      "ttf": "font/ttf", "eot": "application/vnd.ms-fontobject",
                      "json": "application/json"}.get(ext.lstrip("."), "application/octet-stream")
                self.send_response(200)
                self.send_header("Content-Type", ct)
                self.send_header("Cache-Control", "max-age=3600")
                self.end_headers()
                with open(static_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8")
        if self.path == "/save":
            with open(SAVE_FILE, "w") as f:
                f.write(body)
            try:
                with open(SECTION_ID_FILE, "r") as f:
                    sid = f.read().strip()
                if sid:
                    from db.database import update_section_workbook, get_custom_section, save_document_version
                    data = json.loads(body)
                    sheet_data = data.get("sheetData", data.get("sheets", []))
                    wb_json = json.dumps(sheet_data)
                    log_msg(f"SAVE section_id={sid} wb_size={len(sheet_data)} sheets")
                    update_section_workbook(int(sid), wb_json)
                    sec = get_custom_section(int(sid))
                    if sec:
                        doc_id = sec.get("document_id")
                        log_msg(f"SAVE sec_name={sec.get('name')} doc_id={doc_id}")
                        if doc_id:
                            save_document_version(doc_id, wb_json, comment="Editado desde editor")
                            log_msg(f"SAVE version saved doc_id={doc_id}")
                        else:
                            from db.database import create_document
                            doc_id = create_document(name=sec.get("name", "Sección"))
                            save_document_version(doc_id, wb_json, comment="Versión inicial")
                            from db.database import update_custom_section_meta
                            update_custom_section_meta(int(sid), document_id=doc_id)
                            log_msg(f"SAVE new_doc created doc_id={doc_id}")
            except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
                log_msg(f"SAVE_ERROR {e}")
                pass
            self._send_json('{"status":"ok"}')
        elif self.path == "/save_template" and self.engine:
            try:
                data = json.loads(body)
                name = data.get("name", "Plantilla")
                pid = self.engine.get_or_create_project(name)
                self.engine.save_version(pid, json.dumps(data.get("sheetData", [])))
                self._send_json('{"status":"ok","id":' + str(pid) + '}')
            except Exception as e:
                self._send_json('{"status":"error","msg":"' + str(e) + '"}')
        elif self.path == "/create_section":
            try:
                data = json.loads(body)
                from db.database import create_custom_section
                sec_key = data.get("key", "sec_" + str(int(__import__("time").time())))
                columns_json = json.dumps(data.get("columns", []))
                sec_id = create_custom_section(sec_key, data.get("name", "Seccion"), columns_json, data.get("icon", "📄"))
                self._send_json('{"status":"ok","id":' + str(sec_id) + ',"key":"' + sec_key + '"}')
            except Exception as e:
                self._send_json('{"status":"error","msg":"' + str(e).replace('"', "'") + '"}')
        elif self.path == "/save_to_section":
            try:
                data = json.loads(body)
                from db.database import add_custom_section_row
                row_id = add_custom_section_row(data["section_id"], json.dumps(data.get("row_data", {})))
                self._send_json('{"status":"ok","row_id":' + str(row_id) + '}')
            except Exception as e:
                self._send_json('{"status":"error","msg":"' + str(e).replace('"', "'") + '"}')
        elif self.path == "/save_as_section":
            try:
                data = json.loads(body)
                from db.database import create_custom_section, add_custom_section_row, get_custom_section, delete_custom_section
                workbook = data.get("workbook", [])
                sheet = workbook[0] if isinstance(workbook, list) and len(workbook) > 0 else {}

                headers, rows = _extract_sheet_data(sheet)
                if not headers:
                    self._send_json('{"status":"error","msg":"No se pudieron extraer encabezados"}')
                    return

                workbook_json = json.dumps(workbook) if workbook is not None else None
                section_id = data.get("section_id")
                meta_name = data.get("name", "Seccion")
                meta_desc = data.get("description", "")
                meta_color = data.get("color", "#5e81f4")
                meta_type = data.get("type", "spreadsheet")
                if section_id:
                    existing = get_custom_section(section_id)
                    if existing:
                        delete_custom_section(section_id)
                        section_id = create_custom_section(existing["section_key"], existing["name"], json.dumps([{"name": h} for h in headers]), existing.get("icon", "📄"), workbook_json, meta_desc, meta_color, meta_type)
                    else:
                        self._send_json('{"status":"error","msg":"Seccion no encontrada"}')
                        return
                else:
                    key = data.get("key", "sec_" + str(int(__import__("time").time())))
                    section_id = create_custom_section(key, meta_name, json.dumps([{"name": h} for h in headers]), "📄", workbook_json, meta_desc, meta_color, meta_type)

                for row in rows:
                    add_custom_section_row(section_id, json.dumps(row))
                self._send_json('{"status":"ok","section_id":' + str(section_id) + ',"rows":' + str(len(rows)) + '}')
            except Exception as e:
                self._send_json('{"status":"error","msg":"' + str(e).replace('"', "'") + '"}')
        elif self.path == "/delete_section":
            try:
                data = json.loads(body)
                from db.database import delete_custom_section
                delete_custom_section(data["section_id"])
                self._send_json('{"status":"ok"}')
            except Exception as e:
                self._send_json('{"status":"error","msg":"' + str(e).replace('"', "'") + '"}')
        else:
            self._send_json('{"status":"error"}')

    def _send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data.encode("utf-8"))

    def log_message(self, *a):
        pass


class EditorView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.server = None
        self.port = self._find_port()
        self._disabled = QWebEngineView is None
        self._current_doc_id = None
        self._pending_save = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if self._disabled:
            lbl = QLabel("Editor no disponible: Qt WebEngine no esta instalado correctamente.\n"
                         "Ejecuta: pip install PyQtWebEngine")
            lbl.setStyleSheet(f"color: {COLOR_WARNING}; font-size: 14px; padding: 40px;")
            lbl.setAlignment(Qt.AlignCenter)
            layout.addWidget(lbl)
            self.web = None
            return

        toolbar = self._build_toolbar()
        layout.addWidget(toolbar)

        self.web = QWebEngineView()
        self.web.setStyleSheet("border: none;")
        layout.addWidget(self.web)

        self._ls_window = None
        self._watch = QTimer()
        self._watch.timeout.connect(self._check_save)
        self._watch.start(1500)

        self._start_server()

    def _build_toolbar(self):
        bar = QFrame()
        bar.setStyleSheet(f"QFrame {{ background: {COLOR_PANEL}; border-bottom: 1px solid {COLOR_BORDER}; }}")
        h = QHBoxLayout(bar)
        h.setContentsMargins(16, 8, 16, 8)
        h.setSpacing(8)

        lbl = QLabel("Editor de Plantillas")
        lbl.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {COLOR_TEXT};")
        h.addWidget(lbl)

        h.addStretch()

        btn_save = QPushButton("Guardar")
        btn_save.setStyleSheet(f"""
            QPushButton {{ padding: 0 16px; height: 34px; border: none;
                background: {COLOR_ACCENT}; color: #fff; font-size: 12px; font-weight: 600; }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        btn_save.clicked.connect(self._save_current)
        h.addWidget(btn_save)

        btn_new_ver = QPushButton("Guardar como nueva versión")
        btn_new_ver.setStyleSheet(f"""
            QPushButton {{ padding: 0 16px; height: 34px; border: 1px solid {COLOR_ACCENT};
                background: transparent; color: {COLOR_ACCENT}; font-size: 12px; }}
            QPushButton:hover {{ background: {COLOR_ACCENT}15; }}
        """)
        btn_new_ver.clicked.connect(self._save_new_version)
        h.addWidget(btn_new_ver)

        btn_fullscreen = QPushButton("⛶ Pantalla completa")
        btn_fullscreen.setStyleSheet(f"""
            QPushButton {{ padding: 0 12px; height: 34px; border: none;
                background: transparent; color: {COLOR_TEXT_MUTED}; font-size: 12px; }}
            QPushButton:hover {{ background: {COLOR_HOVER}; color: {COLOR_TEXT}; }}
        """)
        btn_fullscreen.clicked.connect(self._toggle_fullscreen)
        h.addWidget(btn_fullscreen)

        btn_close = QPushButton("✕ Cerrar")
        btn_close.setStyleSheet(f"""
            QPushButton {{ padding: 0 14px; height: 34px; border: none;
                background: transparent; color: {COLOR_DANGER}; font-size: 12px; }}
            QPushButton:hover {{ background: #2a1a1a; }}
        """)
        btn_close.clicked.connect(self._close_editor)
        h.addWidget(btn_close)

        self._btn_fullscreen = btn_fullscreen
        return bar

    def _find_port(self):
        import socket
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        return port

    def _start_server(self):
        from engine.meta_engine import MetaEngine
        _Handler.engine = MetaEngine()
        srv = HTTPServer(("127.0.0.1", self.port), _Handler)
        self.server = srv
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()

    def refresh(self):
        self._current_doc_id = None

    def load_workbook(self, workbook_data, doc_id=None):
        if workbook_data is None:
            workbook_data = {"sheetData": [], "name": "Editor"}
        if isinstance(workbook_data, list):
            name = workbook_data[0].get("name", "Editor") if workbook_data else "Editor"
            data = {"name": name, "sheetData": workbook_data}
        else:
            data = workbook_data
        self._current_doc_id = doc_id
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
        try:
            os.remove(SAVE_FILE)
        except FileNotFoundError:
            pass
        if self.web:
            self.web.load(QUrl(f"http://localhost:{self.port}"))

    def _save_current(self):
        self._auto_save_to_doc()
        QMessageBox.information(self, "Guardado", "Documento guardado correctamente.")

    def _save_new_version(self):
        if not self._pending_save:
            QMessageBox.information(self, "Sin cambios", "No hay datos nuevos para guardar.")
            return
        if not self._current_doc_id:
            QMessageBox.warning(self, "Error", "No hay documento abierto.")
            return
        from services import ServiceRegistry
        ss = ServiceRegistry.instance().spreadsheet()
        try:
            data = json.loads(self._pending_save)
            ss.doc_service.save_version(
                self._current_doc_id,
                json.dumps(data.get("sheetData", [])),
                comment="Guardado desde editor"
            )
            self._pending_save = None
            QMessageBox.information(self, "Versión guardada", "Nueva versión creada.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _auto_save_to_doc(self):
        if not self._pending_save or not self._current_doc_id:
            return
        from services import ServiceRegistry
        ss = ServiceRegistry.instance().spreadsheet()
        try:
            data = json.loads(self._pending_save)
            ss.doc_service.save_workbook(
                self._current_doc_id,
                json.dumps(data.get("sheetData", []))
            )
            self._pending_save = None
        except Exception:
            pass

    def _close_editor(self):
        if self._ls_window:
            self._ls_window.close()
            self._ls_window = None
        self._auto_save_to_doc()
        parent = self.parent()
        while parent and not hasattr(parent, "stack"):
            parent = parent.parent() if hasattr(parent, "parent") else None
        if parent and hasattr(parent, "stack") and hasattr(parent, "_view_widgets"):
            if "editor" in parent._view_widgets:
                parent.stack.setCurrentWidget(parent._view_widgets["editor"])
                parent.header_bar.set_breadcrumb("Inicio / Documentos")

    def _check_save(self):
        try:
            with open(SAVE_FILE, "r") as f:
                content = f.read().strip()
            if content:
                self._pending_save = content
                os.remove(SAVE_FILE)
        except FileNotFoundError:
            pass

    def _toggle_fullscreen(self):
        if hasattr(self, "_ls_window") and self._ls_window:
            self._ls_window.close()
            self._ls_window = None
            return
        from widgets.luckysheet_window import LuckySheetWindow
        self._ls_window = LuckySheetWindow(self.port, self)
        self._ls_window.showMaximized()
        self._btn_fullscreen.setText("⛶ Cerrar ventana")

    def on_escape(self):
        if hasattr(self, "_ls_window") and self._ls_window:
            self._ls_window.close()
            self._ls_window = None

    def on_luckysheet_closed(self):
        self._ls_window = None
        self._btn_fullscreen.setText("⛶ Pantalla completa")

