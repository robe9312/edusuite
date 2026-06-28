import os, json, uuid, threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QMessageBox, QFrame, QSizePolicy,
)
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    try:
        from PyQt5.QtWebEngineWidgets import QWebEngineView
    except ImportError:
        QWebEngineView = None

from db.database import (
    get_connection, get_subject, get_distinct_courses,
    get_students_by_course, get_grade, get_active_school_year, get_subjects_by_level,
)
from config import *
from ui_style import Combo

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "luckysheet")
DATA_FILE = "/tmp/edusuite_workbook.json"
SAVE_FILE = "/tmp/edusuite_save.json"


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/data":
            try:
                with open(DATA_FILE, "r") as f:
                    data = f.read()
            except (FileNotFoundError, json.JSONDecodeError):
                data = "{}"
            self._send_json(data)
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
        if self.path == "/save":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            with open(SAVE_FILE, "w") as f:
                f.write(body.decode("utf-8"))
            self._send_json('{"status":"ok"}')

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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
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

        ls = f"color: {COLOR_TEXT_MUTED}; font-size: 12px;"

        lbl = QLabel("Tipo")
        lbl.setStyleSheet(ls)
        h.addWidget(lbl)
        self.cb_type = Combo()
        self.cb_type.addItems(["Hoja en blanco", "Calificaciones", "Matricula"])
        h.addWidget(self.cb_type)

        lbl = QLabel("Nivel")
        lbl.setStyleSheet(ls)
        h.addWidget(lbl)
        self.cb_level = Combo()
        h.addWidget(self.cb_level)

        lbl = QLabel("Asignatura")
        lbl.setStyleSheet(ls)
        h.addWidget(lbl)
        self.cb_subject = Combo()
        h.addWidget(self.cb_subject)

        lbl = QLabel("Periodo")
        lbl.setStyleSheet(ls)
        h.addWidget(lbl)
        self.cb_period = Combo()
        self.cb_period.addItems(["T1", "T2", "T3"])
        h.addWidget(self.cb_period)

        btn_load = QPushButton("Cargar datos")
        btn_load.setStyleSheet(f"""
            QPushButton {{ padding: 0 16px; height: 36px; border: none;
                background: {COLOR_ACCENT}; color: #ffffff; font-size: 13px; }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        btn_load.clicked.connect(self.load_from_db)
        h.addWidget(btn_load)

        btn_fullscreen = QPushButton("⛶ Pantalla completa")
        btn_fullscreen.setStyleSheet(f"""
            QPushButton {{ padding: 0 12px; height: 36px; border: none;
                background: {COLOR_ACCENT}; color: #ffffff; font-size: 12px; }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        btn_fullscreen.clicked.connect(self._toggle_fullscreen)
        h.addWidget(btn_fullscreen)

        btn_import = QPushButton("Importar a DB")
        btn_import.setStyleSheet(f"""
            QPushButton {{ padding: 0 16px; height: 36px; border: none;
                background: {COLOR_SUCCESS}; color: #ffffff; font-size: 13px; }}
            QPushButton:hover {{ background: #5a7e5a; }}
        """)
        btn_import.clicked.connect(self.import_save)
        h.addWidget(btn_import)

        h.addStretch()
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
        srv = HTTPServer(("127.0.0.1", self.port), _Handler)
        self.server = srv
        t = threading.Thread(target=srv.serve_forever, daemon=True)
        t.start()

    def refresh(self):
        self.cb_type.setCurrentIndex(0)
        self.cb_level.currentIndexChanged.connect(self._on_level_change)
        self._refresh_levels()

    def _refresh_levels(self):
        levels = get_distinct_courses()
        self.cb_level.clear()
        self.cb_level.addItem("Todos los niveles")
        for lv in levels:
            self.cb_level.addItem(lv)

    def _on_level_change(self, idx):
        if idx <= 0:
            self.cb_subject.clear()
            return
        level = self.cb_level.currentText()
        subs = get_subjects_by_level(level)
        self.cb_subject.clear()
        for s in subs:
            self.cb_subject.addItem(s["name"], s["id"])

    def load_from_db(self):
        wtype = self.cb_type.currentText()
        if wtype == "Calificaciones":
            data = self._build_grades_data()
        elif wtype == "Matricula":
            data = self._build_enrollment_data()
        else:
            data = {
                "name": "Nuevo libro",
                "sheetData": [{"name": "Hoja1", "celldata": [], "config": {}}]
            }
        if data is None:
            return
        with open(DATA_FILE, "w") as f:
            json.dump(data, f)
        try:
            os.remove(SAVE_FILE)
        except FileNotFoundError:
            pass
        self.web.load(QUrl(f"http://localhost:{self.port}"))
        self._status("Abierto en el editor interno")

    def _build_grades_data(self):
        level = self.cb_level.currentText()
        if level == "Todos los niveles" or not level:
            QMessageBox.warning(self, "Aviso", "Selecciona un nivel.")
            return
        subj_id = self.cb_subject.currentData()
        if not subj_id:
            QMessageBox.warning(self, "Aviso", "Selecciona una asignatura.")
            return
        period = self.cb_period.currentText()
        subject = get_subject(subj_id)
        students = get_students_by_course(level)
        if not students:
            QMessageBox.information(self, "Sin datos", "No hay estudiantes en este nivel.")
            return

        celldata = []
        headers = ["Codigo", "Estudiante", "Curso", f"Nota ({period})", "Obs"]
        for c, h in enumerate(headers):
            celldata.append({"r": 0, "c": c, "v": {"v": h, "m": h, "bg": "#2a2a2a", "fc": "#ffffff"}})
        for i, s in enumerate(students, 1):
            g = get_grade(s["id"], subj_id, period)
            score = g["score"] if g else ""
            obs = g["obs"] if g and g.get("obs") else ""
            celldata.append({"r": i, "c": 0, "v": {"v": s["code"], "m": s["code"]}})
            celldata.append({"r": i, "c": 1, "v": {"v": s["nombre"], "m": s["nombre"]}})
            celldata.append({"r": i, "c": 2, "v": {"v": s.get("curso", ""), "m": s.get("curso", "")}})
            celldata.append({"r": i, "c": 3, "v": {"v": score, "m": str(score)}})
            celldata.append({"r": i, "c": 4, "v": {"v": obs, "m": obs}})

        return {
            "name": f"{subject['name']} - {period}",
            "sheetData": [{"name": f"{subject['name']} {period}", "celldata": celldata}]
        }

    def _build_enrollment_data(self):
        year = get_active_school_year()
        if not year:
            QMessageBox.warning(self, "Aviso", "No hay un ano escolar activo.")
            return
        from db.database import get_enrollments_by_year
        enrollments = get_enrollments_by_year(year["id"])
        celldata = []
        headers = ["Codigo", "Nombre", "Curso", "Nivel", "Total", "Pagado", "Estado"]
        for c, h in enumerate(headers):
            celldata.append({"r": 0, "c": c, "v": {"v": h, "m": h, "bg": "#2a2a2a", "fc": "#ffffff"}})
        for i, e in enumerate(enrollments, 1):
            grade_level = e.get("grade_level", "")
            level_key = COURSE_TO_LEVEL.get(grade_level, "")
            level_name = LEVEL_LABELS.get(level_key, grade_level)
            
            celldata.append({"r": i, "c": 0, "v": {"v": e["student_code"], "m": e["student_code"]}})
            celldata.append({"r": i, "c": 1, "v": {"v": e["student_name"], "m": e["student_name"]}})
            celldata.append({"r": i, "c": 2, "v": {"v": grade_level, "m": grade_level}})
            celldata.append({"r": i, "c": 3, "v": {"v": level_name, "m": level_name}})
            celldata.append({"r": i, "c": 4, "v": {"v": e["total_amount"], "m": str(e["total_amount"])}})
            celldata.append({"r": i, "c": 5, "v": {"v": e["paid_amount"], "m": str(e["paid_amount"])}})
            celldata.append({"r": i, "c": 6, "v": {"v": e["status"], "m": e["status"]}})
        return {
            "name": f"Matricula {year['label']}",
            "sheetData": [{"name": f"Matricula {year['label']}", "celldata": celldata}]
        }

    def _status(self, msg):
        self.setWindowTitle(msg)

    def _check_save(self):
        try:
            with open(SAVE_FILE, "r") as f:
                content = f.read().strip()
            if content:
                self._pending_save = content
                self._status("Datos guardados desde el editor. Clic en 'Importar a DB'.")
                os.remove(SAVE_FILE)
        except FileNotFoundError:
            pass


    def _toggle_fullscreen(self):
        mw = self.window()
        if not hasattr(mw, "_toggle_editor_fullscreen"):
            return
        mw._toggle_editor_fullscreen()

    def on_escape(self):
        mw = self.window()
        if hasattr(mw, "_toggle_editor_fullscreen") and getattr(mw, "_editor_fullscreen", False):
            mw._toggle_editor_fullscreen()

    def import_save(self):
        if not hasattr(self, "_pending_save") or not self._pending_save:
            QMessageBox.information(self, "Sin datos", "No hay datos pendientes. Guarda desde el editor primero.")
            return
        try:
            data = json.loads(self._pending_save)
            from engine.meta_engine import MetaEngine
            engine = MetaEngine()
            project_name = data.get("name", "Editor")
            project_id = engine.get_or_create_project(project_name)
            version_id = engine.save_version(project_id, json.dumps(data.get("sheetData", [])))
            self._pending_save = None
            QMessageBox.information(self, "Importado", f"Datos guardados como versión {version_id} del proyecto '{project_name}'.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

