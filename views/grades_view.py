from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QMessageBox,
    QComboBox, QLineEdit, QHeaderView, QDialog, QRadioButton, QButtonGroup,
    QFrame,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QShortcut, QKeySequence, QUndoStack

from db.database import get_all_students
from config import *
from models.column_definition import build_grade_columns, ColumnType
from models.spreadsheet_model import SpreadsheetTableModel
from models.grade_proxy import GradeProxyModel
from widgets.spreadsheet_view import SpreadsheetView
from widgets.student_panel import StudentPanel
from core.clipboard_engine import ClipboardEngine
from repositories import subject_repo, student_repo, course_repo, grade_repo


EXPORT_MODES = [
    ("course_trimester", "Curso + Trimestre", ""),
    ("course_all", "Curso completo (3T)", ""),
    ("student", "Por alumno", ""),
    ("summary", "Resumen por trimestre", ""),
]


class ExportDialog(QDialog):
    def __init__(self, parent=None, courses=None):
        super().__init__(parent)
        self.setWindowTitle("Exportar Notas")
        self.setMinimumWidth(520)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background: {COLOR_SURFACE}; }}")
        self.courses = courses or []
        self.result_data = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        title = QLabel("Selecciona el tipo de exportación")
        title.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 14px;")
        layout.addWidget(title)
        self.mode_group = QButtonGroup(self)
        mode_layout = QVBoxLayout()
        mode_layout.setSpacing(8)
        self.mode_radios = []
        for key, label, desc in EXPORT_MODES:
            rb = QRadioButton(f" {label}")
            rb.setStyleSheet(f"""
                QRadioButton {{ color: {COLOR_TEXT}; font-size: 13px;
                    padding: 6px 10px; border: 1px solid {COLOR_BORDER};
                    background: {COLOR_INPUT}; }}
                QRadioButton:hover {{ background: {COLOR_HOVER}; }}
                QRadioButton::indicator {{
                    width: 14px; height: 14px; border: 1px solid {COLOR_BORDER};
                    background: {COLOR_INPUT}; }}
                QRadioButton::indicator:checked {{
                    background: {COLOR_ACCENT}; border-color: {COLOR_ACCENT}; }}
            """)
            mode_layout.addWidget(rb)
            self.mode_group.addButton(rb, len(self.mode_radios))
            self.mode_radios.append((key, rb))
        layout.addLayout(mode_layout)

        opts = QHBoxLayout()
        opts.setSpacing(12)
        for label, attr, items in [
            ("Curso:", "course_combo", True),
            ("Trimestre:", "period_combo", ["T1", "T2", "T3"]),
        ]:
            ol = QVBoxLayout()
            ol.setSpacing(4)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
            ol.addWidget(lbl)
            combo = QComboBox()
            combo.setStyleSheet(f"QComboBox {{ background: {COLOR_INPUT}; border: 1px solid {COLOR_BORDER}; color: {COLOR_TEXT}; padding: 4px 8px; min-height: 28px; }}")
            if isinstance(items, list):
                combo.addItems(items)
            else:
                combo.addItems(self.courses)
            ol.addWidget(combo)
            opts.addLayout(ol)
            setattr(self, attr, combo)

        sl = QVBoxLayout()
        sl.setSpacing(4)
        sl.addWidget(QLabel("Alumno:"))
        sl.itemAt(0).widget().setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        self.student_combo = QComboBox()
        self.student_combo.setStyleSheet(f"QComboBox {{ background: {COLOR_INPUT}; border: 1px solid {COLOR_BORDER}; color: {COLOR_TEXT}; padding: 4px 8px; min-height: 28px; }}")
        students = get_all_students()
        for s in students:
            self.student_combo.addItem(f"{s.get('code','')} - {s.get('nombre','')}", s["id"])
        sl.addWidget(self.student_combo)
        opts.addLayout(sl)
        layout.addLayout(opts)

        self.mode_group.buttonClicked.connect(self._on_mode_change)
        self._on_mode_change()

        btns = QHBoxLayout()
        btns.addStretch()
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet(f"QPushButton {{ padding: 0 24px; height: 36px; border: none; background: transparent; color: {COLOR_TEXT_MUTED}; font-size: 13px; }} QPushButton:hover {{ background: {COLOR_HOVER}; }}")
        cancel_btn.clicked.connect(self.reject)
        export_btn = QPushButton("Exportar")
        export_btn.setStyleSheet(f"QPushButton {{ padding: 0 24px; height: 36px; border: none; background: {COLOR_ACCENT}; color: #ffffff; font-size: 13px; }} QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}")
        export_btn.clicked.connect(self._accept)
        btns.addWidget(cancel_btn)
        btns.addWidget(export_btn)
        layout.addLayout(btns)

    def _on_mode_change(self):
        btn_id = self.mode_group.checkedId()
        if btn_id < 0:
            btn_id = 0
        key = self.mode_radios[btn_id][0]
        self.course_combo.parent().setVisible(key in ("course_trimester", "course_all"))
        self.period_combo.parent().setVisible(key in ("course_trimester", "summary"))
        self.student_combo.parent().setVisible(key == "student")

    def _accept(self):
        btn_id = self.mode_group.checkedId()
        if btn_id < 0:
            QMessageBox.warning(self, "Selecciona", "Elige un tipo de exportación.")
            return
        key = self.mode_radios[btn_id][0]
        data = {"mode": key}
        if key in ("course_trimester", "course_all"):
            data["course"] = self.course_combo.currentText()
        if key in ("course_trimester", "summary"):
            data["period"] = self.period_combo.currentText()
        if key == "student":
            data["student_id"] = self.student_combo.currentData()
        self.result_data = data
        self.accept()


class StatBadge(QFrame):
    def __init__(self, label, value="—", color=COLOR_TEXT):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(0)
        self.val_lbl = QLabel(str(value))
        self.val_lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color};")
        layout.addWidget(self.val_lbl)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 10px;")
        layout.addWidget(lbl)


class GradesView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._current_subjects = []
        self._students_data = []
        self._model = None
        self._proxy = None
        self._undo_stack = QUndoStack()
        self._clipboard = None
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(200)
        self._search_timer.timeout.connect(self._apply_search)
        self._build()
        QShortcut(QKeySequence("Ctrl+S"), self, self._save_all)
        QShortcut(QKeySequence("Ctrl+Z"), self, self._undo_stack.undo)
        QShortcut(QKeySequence("Ctrl+Shift+Z"), self, self._undo_stack.redo)

    def _build(self):
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        main_area = QWidget()
        layout = QVBoxLayout(main_area)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        header = QLabel("Libro de Calificaciones")
        header.setStyleSheet(f"font-size: 20px; font-weight: 600; color: {COLOR_TEXT};")
        layout.addWidget(header)

        filter_bar = QHBoxLayout()
        filter_bar.setSpacing(10)

        for lbl, attr, items in [
            ("Curso:", "course_combo", True),
            ("Trimestre:", "period_combo", PERIODS),
        ]:
            l = QLabel(lbl)
            l.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 11px;")
            filter_bar.addWidget(l)
            combo = QComboBox()
            combo.setStyleSheet(f"QComboBox {{ background: {COLOR_INPUT}; border: 1px solid {COLOR_BORDER}; color: {COLOR_TEXT}; padding: 4px 10px; min-height: 30px; min-width: 80px; }} QComboBox:focus {{ border-color: {COLOR_ACCENT}; }}")
            setattr(self, attr, combo)
            filter_bar.addWidget(combo)

        self.course_combo.currentTextChanged.connect(self._load_grades)
        self.period_combo.currentTextChanged.connect(self._load_grades)

        filter_bar.addStretch()

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Buscar alumno...")
        self._search_input.setFixedWidth(200)
        self._search_input.setFixedHeight(32)
        self._search_input.textChanged.connect(self._on_search)
        self._search_input.setStyleSheet(f"QLineEdit {{ background: {COLOR_INPUT}; border: 1px solid {COLOR_BORDER}; color: {COLOR_TEXT}; font-size: 12px; padding: 0 12px; }} QLineEdit:focus {{ border-color: {COLOR_ACCENT}; }}")
        filter_bar.addWidget(self._search_input)

        self.save_btn = QPushButton("Guardar")
        self.save_btn.setStyleSheet(f"QPushButton {{ padding: 0 16px; height: 32px; border: none; background: {COLOR_SUCCESS}; color: #ffffff; font-size: 12px; }} QPushButton:hover {{ background: #3d9142; }}")
        self.save_btn.clicked.connect(self._save_all)
        filter_bar.addWidget(self.save_btn)

        export_btn = QPushButton("Exportar")
        export_btn.setStyleSheet(f"QPushButton {{ padding: 0 16px; height: 32px; border: none; background: {COLOR_ACCENT}; color: #ffffff; font-size: 12px; }} QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}")
        export_btn.clicked.connect(self._export_dialog)
        filter_bar.addWidget(export_btn)

        layout.addLayout(filter_bar)

        self.spreadsheet = SpreadsheetView()
        self.spreadsheet.main_table.clicked.connect(self._on_row_click)
        self.spreadsheet.frozen_table.clicked.connect(self._on_row_click)
        layout.addWidget(self.spreadsheet, 1)

        self._clipboard = ClipboardEngine(self.spreadsheet)
        for t in [self.spreadsheet.frozen_table, self.spreadsheet.main_table]:
            QShortcut(QKeySequence("Ctrl+C"), t, self._clipboard.copy)
            QShortcut(QKeySequence("Ctrl+V"), t, self._clipboard.paste)
            QShortcut(QKeySequence("Ctrl+X"), t, self._clipboard.cut)
            QShortcut(QKeySequence("Delete"), t, self._clipboard.delete_selection)

        footer = QHBoxLayout()
        self._footer_frame = QWidget()
        self._footer_layout = QHBoxLayout(self._footer_frame)
        self._footer_layout.setContentsMargins(0, 0, 0, 0)
        self._footer_layout.setSpacing(24)
        footer.addWidget(self._footer_frame)
        footer.addStretch()
        layout.addLayout(footer)

        outer.addWidget(main_area, 1)

        self.student_panel = StudentPanel()
        self.student_panel.close_btn.clicked.connect(self._close_panel)
        outer.addWidget(self.student_panel)

    def _on_search(self, text):
        self._search_timer.start()

    def _apply_search(self):
        text = self._search_input.text().strip().lower()
        if self._proxy:
            self._proxy.set_search_text(text)

    def _on_row_click(self, index):
        row = index.row()
        if self._proxy:
            src_idx = self._proxy.mapToSource(index)
            row = src_idx.row()
        if row < 0 or row >= len(self._students_data):
            return
        self.student_panel.show_student(self._students_data[row])

    def _close_panel(self):
        self.student_panel.hide_panel()

    def _load_grades(self):
        course = self.course_combo.currentText()
        period = self.period_combo.currentText()
        if not course:
            self.spreadsheet.setModel(None)
            return

        students = student_repo.by_course(course)
        subjects = subject_repo.for_course(course)
        self._current_subjects = subjects
        self._students_data = students

        if not subjects or not students:
            self.spreadsheet.setModel(None)
            return

        cols, _ = build_grade_columns(subjects, period)

        def load_cell(row_id, col_def):
            meta = col_def.meta
            if "subject_id" in meta and "period" in meta:
                g = grade_repo.get_grade(row_id, meta["subject_id"], meta["period"])
                if g:
                    try:
                        return float(g["score"])
                    except (ValueError, TypeError):
                        pass
            return None

        def save_cell(row_id, col_id, val):
            for col in cols:
                if col.id == col_id and col.meta:
                    meta = col.meta
                    if "subject_id" in meta and "period" in meta:
                        if val is not None:
                            grade_repo.set_grade(row_id, meta["subject_id"], meta["period"], val)
                        return

        self._model = SpreadsheetTableModel(
            cols, students,
            load_cell_fn=load_cell,
            save_cell_fn=save_cell,
            undo_stack=self._undo_stack,
            repo=grade_repo,
        )
        self._proxy = GradeProxyModel()
        self._proxy.setSourceModel(self._model)
        self.spreadsheet.setModel(self._proxy)
        self._apply_search()
        self._update_footer()

    def _on_selection_changed(self):
        pass

    def _update_footer(self):
        while self._footer_layout.count():
            item = self._footer_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if not self._model or not self._students_data:
            return
        avgs = []
        for stu in self._students_data:
            sid = stu.get("id", 0)
            vals = [v for v in self._model._data.get(sid, {}).values() if v is not None]
            if vals:
                avgs.append(round(sum(vals) / len(vals), 1))
        if avgs:
            prom = round(sum(avgs) / len(avgs), 1)
            a = sum(1 for a in avgs if a >= 5.0)
            s = len(avgs) - a
            for text, color in [
                (f"Promedio curso: {prom}", COLOR_TEXT),
                (f"Aprobados: {a}", COLOR_SUCCESS),
                (f"Suspensos: {s}", COLOR_DANGER),
                (f"Media: {prom}", COLOR_TEXT_MUTED),
            ]:
                lbl = QLabel(text)
                lbl.setStyleSheet(f"color: {color}; font-size: 13px; font-weight: bold;")
                self._footer_layout.addWidget(lbl)

    def _save_all(self):
        if not self._model:
            return
        count = self._model.dirty_count()
        self._model.save_dirty()
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Guardado")
        msg.setText(f"{count} notas guardadas." if count else "Sin cambios.")
        msg.exec()
        self.main.refresh_stats()

    def _export_dialog(self):
        courses = course_repo.all_distinct()
        if not courses:
            QMessageBox.warning(self, "Sin datos", "No hay cursos.")
            return
        dlg = ExportDialog(self, courses)
        if dlg.exec() != QDialog.Accepted or not dlg.result_data:
            return
        data = dlg.result_data
        mode = data.get("mode")
        try:
            from exporters.excel_exporter import (
                export_grades_to_excel, export_grades_by_course_and_trimester,
                export_grades_by_student, export_grades_summary_by_trimester,
            )
            path = None
            if mode == "course_trimester":
                path = export_grades_by_course_and_trimester(data["course"], data["period"])
            elif mode == "course_all":
                path = export_grades_to_excel(data["course"])
            elif mode == "student":
                path = export_grades_by_student(data["student_id"])
            elif mode == "summary":
                path = export_grades_summary_by_trimester(data["period"])
            if path:
                QMessageBox.information(self, "Exportado", f"Excel generado:\n{path}")
            else:
                QMessageBox.warning(self, "Sin datos", "No se encontraron datos.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo exportar:\n{e}")

    def show_student_panel(self, student_data):
        self.student_panel.show_student(student_data)

    def on_escape(self):
        self._close_panel()

    def refresh(self):
        current_course = self.course_combo.currentText()
        self.course_combo.blockSignals(True)
        self.course_combo.clear()
        courses = course_repo.all_distinct()
        self.course_combo.addItems(courses)
        if current_course in courses:
            self.course_combo.setCurrentText(current_course)
        elif courses:
            self.course_combo.setCurrentText(courses[0])
        self.course_combo.blockSignals(False)
        self._load_grades()
