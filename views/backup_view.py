import os
import shutil
import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QFileDialog, QFrame, QTextEdit,
)
from PySide6.QtCore import Qt

from db.database import get_db_path
from config import *
from ui_style import Header, Panel


class BackupView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)

        h = Header("Backup y Restauracion")
        layout.addWidget(h)

        info = QLabel(
            "Base de datos: school.db - un solo archivo autocontenido."
        )
        info.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px; padding: 4px 0;")
        info.setWordWrap(True)
        layout.addWidget(info)

        backup_panel = Panel()
        bc = backup_panel.layout()

        backup_btn = QPushButton("Hacer Backup Local")
        backup_btn.setStyleSheet(f"""
            QPushButton {{ padding: 0 16px; height: 36px; border: none;
                background: {COLOR_ACCENT}; color: #ffffff; font-size: 13px; text-align: left; }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        backup_btn.clicked.connect(self._local_backup)
        bc.addWidget(backup_btn)

        restore_btn = QPushButton("Restaurar desde archivo .db")
        restore_btn.setStyleSheet(f"""
            QPushButton {{ padding: 0 16px; height: 36px; border: none;
                background: {COLOR_WARNING}; color: #ffffff; font-size: 13px; text-align: left; }}
            QPushButton:hover {{ background: #c69500; }}
        """)
        restore_btn.clicked.connect(self._local_restore)
        bc.addWidget(restore_btn)

        layout.addWidget(backup_panel)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(140)
        self.log.setStyleSheet(f"""
            QTextEdit {{
                background: {COLOR_INPUT}; color: {COLOR_TEXT_MUTED};
                border: 1px solid {COLOR_BORDER};
                font-family: {HEADER_FONT}; font-size: 11px; padding: 8px;
            }}
        """)
        self.log.append("Historial de operaciones:")
        layout.addWidget(self.log)

        layout.addStretch()

    def _local_backup(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de backup")
        if not folder:
            return
        try:
            db_path = get_db_path()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_name = f"school_{timestamp}.db"
            backup_path = os.path.join(folder, backup_name)
            shutil.copy2(db_path, backup_path)
            self.log.append(f"Backup creado: {backup_path}")
            QMessageBox.information(self, "Backup completado", f"Copia guardada en:\n{backup_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _local_restore(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar archivo .db", "", "Base de datos (*.db)"
        )
        if not path:
            return
        resp = QMessageBox.question(
            self, "Restaurar backup",
            "Restaurar? Se reemplazara la base de datos actual.\n"
            "Se recomienda hacer un backup antes.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp != QMessageBox.Yes:
            return
        try:
            db_path = get_db_path()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            auto_backup = f"{db_path}.{timestamp}.pre_restore"
            shutil.copy2(db_path, auto_backup)
            shutil.copy2(path, db_path)
            self.log.append(f"Restaurado desde: {path}")
            self.log.append(f"   Backup previo: {auto_backup}")
            QMessageBox.information(
                self, "Restauracion completada",
                f"Base de datos restaurada.\nBackup previo: {auto_backup}",
            )
            self.main.refresh_stats()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def refresh(self):
        pass
