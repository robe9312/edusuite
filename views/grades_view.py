from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QLabel, QMessageBox,
    QComboBox, QFrame, QDialog, QRadioButton, QButtonGroup,
)
from PySide6.QtCore import Qt

from db.database import (
    get_students_by_course, upsert_grade, get_grade,
    get_distinct_courses, get_subjects_for_course, get_subjects_by_group,
    get_all_students,
)
from config import *
from ui_style import Combo, Table, Header

PERIODS = ["T1", "T2", "T3"]
PERIOD_SPAN_LABELS = {"T1": "PRIMER TRIMESTRE", "T2": "SEGUNDO TRIMESTRE", "T3": "TERCER TRIMESTRE"}

EXPORT_MODES = [
    ("course_trimester", "Curso + Trimestre", "Una hoja por curso y trimestre"),
    ("course_all", "Curso completo (3T)", "Todas las asignaturas y trimestres"),
    ("student", "Por alumno", "Expediente completo de un alumno"),
    ("summary", "Resumen por trimestre", "Todas las materias, todos los cursos"),
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
                QRadioButton {{
                    color: {COLOR_TEXT}; font-size: 13px; padding: 6px 10px;
                    border: 1px solid {COLOR_BORDER}; background: {COLOR_INPUT};
                }}
                QRadioButton:hover {{ background: {COLOR_HOVER}; }}
                QRadioButton::indicator {{
                    width: 14px; height: 14px; border: 1px solid {COLOR_BORDER};
                    background: {COLOR_INPUT};
                }}
                QRadioButton::indicator:checked {{
                    background: {COLOR_ACCENT}; border-color: {COLOR_ACCENT};
                }}
            """)
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet(f"color: {COLOR_TEXT_DIM}; font-size: 11px; padding-left: 26px;")
            item_w = QVBoxLayout()
            item_w.setSpacing(0)
            item_w.addWidget(rb)
            item_w.addWidget(desc_lbl)
            mode_layout.addLayout(item_w)
            self.mode_group.addButton(rb, len(self.mode_radios))
            self.mode_radios.append((key, rb))

        layout.addLayout(mode_layout)

        opts = QHBoxLayout()
        opts.setSpacing(12)

        ol = QVBoxLayout()
        ol.setSpacing(4)
        ol.addWidget(QLabel("Curso:"))
        ol.itemAt(0).widget().setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        self.course_combo = Combo()
        self.course_combo.addItems(self.courses)
        ol.addWidget(self.course_combo)
        opts.addLayout(ol)

        pl = QVBoxLayout()
        pl.setSpacing(4)
        pl.addWidget(QLabel("Trimestre:"))
        pl.itemAt(0).widget().setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        self.period_combo = Combo()
        self.period_combo.addItems(["T1", "T2", "T3"])
        pl.addWidget(self.period_combo)
        opts.addLayout(pl)

        sl = QVBoxLayout()
        sl.setSpacing(4)
        sl.addWidget(QLabel("Alumno:"))
        sl.itemAt(0).widget().setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        self.student_combo = Combo()
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
        cancel_btn.setStyleSheet(f"""
            QPushButton {{ padding: 0 24px; height: 36px; border: none;
                background: transparent; color: {COLOR_TEXT_MUTED}; font-size: 13px; }}
            QPushButton:hover {{ background: {COLOR_HOVER}; }}
        """)
        cancel_btn.clicked.connect(self.reject)

        export_btn = QPushButton("Exportar")
        export_btn.setStyleSheet(f"""
            QPushButton {{ padding: 0 24px; height: 36px; border: none;
                background: {COLOR_ACCENT}; color: #ffffff; font-size: 13px; }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        export_btn.clicked.connect(self._accept)

        btns.addWidget(cancel_btn)
        btns.addWidget(export_btn)
        layout.addLayout(btns)

    def _on_mode_change(self):
        btn_id = self.mode_group.checkedId()
        if btn_id < 0:
            btn_id = 0
        key = self.mode_radios[btn_id][0]
        show_course = key in ("course_trimester", "course_all")
        show_period = key in ("course_trimester", "summary")
        show_student = key == "student"
        self.course_combo.parent().setVisible(show_course)
        self.period_combo.parent().setVisible(show_period)
        self.student_combo.parent().setVisible(show_student)

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


class GradesView(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main = main_window
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        h = Header("Registro de Notas")
        layout.addWidget(h)

        filters = QHBoxLayout()
        filters.setSpacing(10)

        fl = QLabel("Curso:")
        fl.setStyleSheet(f"color: {COLOR_TEXT_MUTED}; font-size: 12px;")
        filters.addWidget(fl)

        self.course_combo = Combo()
        self.course_combo.currentTextChanged.connect(self._load_grades)
        filters.addWidget(self.course_combo)

        filters.addStretch()

        save_btn = QPushButton("Guardar Todo")
        save_btn.setStyleSheet(f"""
            QPushButton {{
                padding: 0 16px; height: 36px; border: none;
                background: {COLOR_SUCCESS}; color: #ffffff; font-size: 13px;
            }}
            QPushButton:hover {{ background: #3d9142; }}
        """)
        save_btn.clicked.connect(self._save_all)
        filters.addWidget(save_btn)

        export_btn = QPushButton("Exportar Excel")
        export_btn.setStyleSheet(f"""
            QPushButton {{
                padding: 0 16px; height: 36px; border: none;
                background: {COLOR_ACCENT}; color: #ffffff; font-size: 13px;
            }}
            QPushButton:hover {{ background: {COLOR_ACCENT_HOVER}; }}
        """)
        export_btn.clicked.connect(self._export_dialog)
        filters.addWidget(export_btn)

        layout.addLayout(filters)

        self.grades_table = Table()
        self.grades_table.setAlternatingRowColors(False)
        layout.addWidget(self.grades_table)

    def _clear_table(self):
        self.grades_table.clear()
        self.grades_table.setRowCount(0)
        self.grades_table.setColumnCount(0)

    def _load_grades(self):
        course = self.course_combo.currentText()
        if not course:
            self._clear_table()
            return

        students = get_students_by_course(course)
        subjects = get_subjects_for_course(course)
        if not subjects:
            level_key = COURSE_TO_LEVEL.get(course)
            if level_key:
                subjects = get_subjects_by_group(level_key)

        n_sub = len(subjects)
        if n_sub == 0:
            self._clear_table()
            return

        n_cols = 2 + n_sub * 3
        n_rows = len(students)

        self.grades_table.setColumnCount(n_cols)
        self.grades_table.setRowCount(n_rows + 2)

        header_font = "font-size: 10px; letter-spacing: 1px;"

        for c in range(n_cols):
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemIsEnabled)
            self.grades_table.setItem(0, c, item)
            item2 = QTableWidgetItem()
            item2.setFlags(Qt.ItemIsEnabled)
            self.grades_table.setItem(1, c, item2)

        self.grades_table.setSpan(0, 0, 2, 1)
        self.grades_table.setSpan(0, 1, 2, 1)
        self._set_header_cell(0, 0, "CÓDIGO")
        self._set_header_cell(0, 1, "ESTUDIANTE")

        for pi, period in enumerate(PERIODS):
            start_col = 2 + pi * n_sub
            end_col = start_col + n_sub - 1
            self.grades_table.setSpan(0, start_col, 1, n_sub)
            period_label = PERIOD_SPAN_LABELS.get(period, period)
            self._set_header_cell(0, start_col, period_label)

            for si, subj in enumerate(subjects):
                col = start_col + si
                self._set_header_cell(1, col, subj["name"].upper())

        self._subject_column_map = {}
        for pi, period in enumerate(PERIODS):
            for si, subj in enumerate(subjects):
                col = 2 + pi * n_sub + si
                self._subject_column_map[col] = {
                    "student_id": None,
                    "subject_id": subj["id"],
                    "period": period,
                }

        self._current_subjects = subjects

        for row, stu in enumerate(students, start=2):
            code_item = QTableWidgetItem(stu.get("code", ""))
            code_item.setFlags(code_item.flags() & ~Qt.ItemIsEditable)
            self.grades_table.setItem(row, 0, code_item)

            name_item = QTableWidgetItem(stu.get("nombre", ""))
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            name_item.setToolTip(stu.get("nombre", ""))
            self.grades_table.setItem(row, 1, name_item)

            for pi, period in enumerate(PERIODS):
                for si, subj in enumerate(subjects):
                    col = 2 + pi * n_sub + si
                    g = get_grade(stu["id"], subj["id"], period)
                    cell = QTableWidgetItem()
                    if g:
                        score = float(g["score"])
                        cell.setData(Qt.DisplayRole, score)
                    cell.setData(Qt.UserRole, {
                        "student_id": stu["id"],
                        "subject_id": subj["id"],
                        "period": period,
                    })
                    self.grades_table.setItem(row, col, cell)

        self.grades_table.setColumnWidth(0, 90)
        self.grades_table.setColumnWidth(1, 260)
        col_width = max(70, 900 // max(n_sub, 1))
        for c in range(2, n_cols):
            self.grades_table.setColumnWidth(c, col_width)

        self.grades_table.setRowHeight(0, 28)
        self.grades_table.setRowHeight(1, 28)

        self.grades_table.setSelectionMode(QTableWidget.SingleSelection)
        self.grades_table.setSelectionBehavior(QTableWidget.SelectItems)

    def _set_header_cell(self, row, col, text):
        item = self.grades_table.item(row, col)
        if item is None:
            item = QTableWidgetItem()
            item.setFlags(Qt.ItemIsEnabled)
            self.grades_table.setItem(row, col, item)
        item.setText(text)
        item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        bg = COLOR_PANEL if row == 0 else COLOR_SURFACE
        item.setBackground(bg)
        fg = COLOR_TEXT if row == 0 else COLOR_TEXT_MUTED
        item.setForeground(fg)

    def _save_all(self):
        course = self.course_combo.currentText()
        if not course:
            QMessageBox.warning(self, "Sin datos", "Selecciona un curso primero.")
            return

        saved = 0
        errors = 0
        n_rows = self.grades_table.rowCount()
        n_cols = self.grades_table.columnCount()

        for row in range(2, n_rows):
            for col in range(2, n_cols):
                item = self.grades_table.item(row, col)
                if item is None:
                    continue
                meta = item.data(Qt.UserRole)
                if not meta:
                    continue
                raw = item.text().strip()
                if not raw:
                    continue
                try:
                    score = float(raw)
                    if score < MIN_SCORE or score > MAX_SCORE:
                        continue
                    upsert_grade(meta["student_id"], meta["subject_id"],
                                 meta["period"], score)
                    saved += 1
                except ValueError:
                    errors += 1

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Guardado")
        text = f"{saved} notas guardadas."
        if errors:
            text += f" {errors} celdas ignoradas (valor inválido)."
        msg.setText(text)
        msg.exec()
        self.main.refresh_stats()

    def _export_dialog(self):
        courses = get_distinct_courses()
        if not courses:
            QMessageBox.warning(self, "Sin datos", "No hay cursos disponibles.")
            return
        dlg = ExportDialog(self, courses)
        if dlg.exec() != QDialog.Accepted or not dlg.result_data:
            return
        data = dlg.result_data
        mode = data.get("mode")

        try:
            path = None
            from exporters.excel_exporter import (
                export_grades_to_excel,
                export_grades_by_course_and_trimester,
                export_grades_by_student,
                export_grades_summary_by_trimester,
            )

            if mode == "course_trimester":
                path = export_grades_by_course_and_trimester(data["course"], data["period"])
            elif mode == "course_all":
                path = export_grades_to_excel(data["course"])
            elif mode == "student":
                path = export_grades_by_student(data["student_id"])
            elif mode == "summary":
                path = export_grades_summary_by_trimester(data["period"])

            if path:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Exportado")
                msg.setText(f"Excel generado:\n{path}")
                msg.exec()
            else:
                QMessageBox.warning(self, "Sin datos", "No se encontraron datos para exportar.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo exportar:\n{e}")

    def refresh(self):
        current_course = self.course_combo.currentText()
        self.course_combo.blockSignals(True)
        self.course_combo.clear()
        courses = get_distinct_courses()
        self.course_combo.addItems(courses)
        if current_course in courses:
            self.course_combo.setCurrentText(current_course)
        elif courses:
            self.course_combo.setCurrentText(courses[0])
        self.course_combo.blockSignals(False)
        self._load_grades()
