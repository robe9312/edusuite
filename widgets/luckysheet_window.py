from PySide6.QtCore import Qt, QUrl
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
except ImportError:
    try:
        from PyQt5.QtWebEngineWidgets import QWebEngineView
    except ImportError:
        QWebEngineView = None


class LuckySheetWindow(QMainWindow):
    def __init__(self, port, parent=None):
        super().__init__(parent)
        self._port = port
        self._returning = False

        self.setWindowTitle("EduSuite Editor — Pantalla completa")
        self.setMinimumSize(800, 600)
        self.resize(1400, 900)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.web = QWebEngineView()
        self.web.setStyleSheet("border: none;")
        layout.addWidget(self.web)

        self.web.load(QUrl(f"http://localhost:{self._port}"))

    def closeEvent(self, event):
        self._returning = True
        parent = self.parent()
        while parent and not hasattr(parent, "on_luckysheet_closed"):
            parent = parent.parent() if hasattr(parent, "parent") else None
        if parent and hasattr(parent, "on_luckysheet_closed"):
            parent.on_luckysheet_closed()
        event.accept()
