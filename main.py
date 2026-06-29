#!/usr/bin/env python3
import sys
import os
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from logs.logger import log

from views.main_window import MainWindow
from views.login_dialog import LoginDialog
from db.database import init_db
from ui_style import apply_global_style
from logs.logger import log_startup


def _excepthook(exc_type, exc_value, exc_tb):
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    log(f"CRASH: {msg}")
    traceback.print_exception(exc_type, exc_value, exc_tb)

sys.excepthook = _excepthook


def main():
    init_db()
    log_startup()

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("EduSuite")
    app.setStyle("Fusion")

    font = app.font()
    font.setPointSize(10)
    app.setFont(font)

    apply_global_style(app)

    login = LoginDialog()
    if login.exec() != LoginDialog.Accepted:
        sys.exit(0)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
