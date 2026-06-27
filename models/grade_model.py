from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QTimer
from PySide6.QtGui import QColor, QUndoStack

from config import PERIODS, heatmap_color, heatmap_text_color, COLOR_TEXT, COLOR_TEXT_MUTED, COLOR_PANEL, COLOR_BORDER

FROZEN_COLS = 3
SUB_COLS = 4


class GradeTableModel(QAbstractTableModel):
    def __init__(self, subjects, period, students_data, grade_fn, undo_stack=None, repo=None):
        super().__init__()
        self._subjects = subjects
        self._period = period
        self._students = students_data
        self._grade_fn = grade_fn
        self._grades = {}
        self._dirty = set()
        self._undo_stack = undo_stack or QUndoStack()
        self._repo = repo
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(800)
        self._save_timer.timeout.connect(self._flush_dirty)
        self._load_grades()

    def _load_grades(self):
        for stu in self._students:
            sid = stu["id"]
            row_data = {}
            for subj in self._subjects:
                sub_id = subj["id"]
                g = self._grade_fn(sid, sub_id, self._period)
                row_data[sub_id] = float(g["score"]) if g else None
            self._grades[sid] = row_data

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._students)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else FROZEN_COLS + len(self._subjects) * SUB_COLS

    def _subject_for_col(self, col):
        if col < FROZEN_COLS:
            return None, None, None
        idx = col - FROZEN_COLS
        si = idx // SUB_COLS
        sub_col = idx % SUB_COLS
        if si >= len(self._subjects):
            return None, None, None
        return self._subjects[si], si, sub_col

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Vertical:
            if role == Qt.DisplayRole:
                return str(section + 1)
            return None

        if role == Qt.DisplayRole:
            if section < FROZEN_COLS:
                return ["Código", "Estudiante", "Curso"][section]
            subj, si, sub_col = self._subject_for_col(section)
            if subj:
                if sub_col < 3:
                    return PERIODS[sub_col] if sub_col < len(PERIODS) else "?"
                return "Prom"
        return None

    def _student_avg(self, stu_id):
        vals = [v for v in self._grades.get(stu_id, {}).values() if v is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    def _subject_avg(self, subj_id):
        vals = []
        for stu in self._students:
            v = self._grades.get(stu["id"], {}).get(subj_id)
            if v is not None:
                vals.append(v)
        return round(sum(vals) / len(vals), 1) if vals else None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        row, col = index.row(), index.column()
        if row >= len(self._students):
            return None
        stu = self._students[row]

        if role == Qt.DisplayRole or role == Qt.EditRole:
            if col < FROZEN_COLS:
                return {0: stu.get("code", ""), 1: stu.get("nombre", ""), 2: stu.get("course", "")}.get(col, "")
            subj, si, sub_col = self._subject_for_col(col)
            if not subj:
                return None
            g = self._grades.get(stu["id"], {}).get(subj["id"])
            if sub_col < 3:
                return g
            avg = self._student_avg(stu["id"])
            return avg

        if role == Qt.TextAlignmentRole:
            if col >= FROZEN_COLS:
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        if role == Qt.ForegroundRole:
            if col < FROZEN_COLS:
                return QColor(COLOR_TEXT)
            subj, si, sub_col = self._subject_for_col(col)
            if not subj:
                return QColor(COLOR_TEXT_MUTED)
            sid = stu["id"]
            if sub_col < 3:
                score = self._grades.get(sid, {}).get(subj["id"])
                return QColor(heatmap_text_color(score))
            avg = self._student_avg(sid)
            return QColor(heatmap_text_color(avg))

        if role == Qt.BackgroundRole:
            if col < FROZEN_COLS:
                return QColor(COLOR_PANEL)
            subj, si, sub_col = self._subject_for_col(col)
            if not subj:
                return QColor(COLOR_PANEL)
            sid = stu["id"]
            if sub_col < 3:
                score = self._grades.get(sid, {}).get(subj["id"])
                return QColor(heatmap_color(score))
            avg = self._student_avg(sid)
            return QColor(heatmap_color(avg))

        if role == Qt.UserRole:
            if col < FROZEN_COLS:
                return None
            subj, si, sub_col = self._subject_for_col(col)
            if not subj or sub_col >= 3:
                return None
            return {"student_id": stu["id"], "subject_id": subj["id"], "period": self._period}

        if role == Qt.ToolTipRole:
            if col < FROZEN_COLS:
                return None
            subj, si, sub_col = self._subject_for_col(col)
            if not subj:
                return None
            sid = stu["id"]
            g = self._grades.get(sid, {}).get(subj["id"])
            if g is not None:
                return f"{subj['name']}: {g}"
            return f"{subj['name']}: —"

        return None

    def setData(self, index, value, role=Qt.EditRole):
        if role != Qt.EditRole:
            return False
        row, col = index.row(), index.column()
        if row >= len(self._students) or col < FROZEN_COLS:
            return False
        subj, si, sub_col = self._subject_for_col(col)
        if not subj or sub_col >= 3:
            return False
        try:
            score = float(value)
            if score < 0 or score > 10:
                return False
        except (ValueError, TypeError):
            return False
        stu = self._students[row]
        sid, sub_id = stu["id"], subj["id"]
        old_score = self._grades.get(sid, {}).get(sub_id)
        if old_score == score:
            return False
        if self._undo_stack:
            from core.undo_commands import SetGradeCommand
            cmd = SetGradeCommand(sid, sub_id, self._period, score, old_score, model=self, repo=self._repo)
            self._undo_stack.push(cmd)
        else:
            self._grades[sid][sub_id] = score
            self._mark_dirty(sid, sub_id)
            self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.ForegroundRole, Qt.BackgroundRole])
            self._update_averages(row)
        return True

    def _mark_dirty(self, student_id, subject_id):
        self._dirty.add((student_id, subject_id, self._period))
        self._save_timer.start()

    def _flush_dirty(self):
        if not self._dirty or not self._repo:
            return
        for sid, sub_id, period in list(self._dirty):
            score = self._grades.get(sid, {}).get(sub_id)
            if score is not None:
                self._repo.set_grade(sid, sub_id, period, score)
        self._dirty.clear()

    def dirty_count(self):
        return len(self._dirty)

    def save_dirty(self):
        if self._save_timer.isActive():
            self._save_timer.stop()
        self._flush_dirty()

    def _update_averages(self, row):
        n = self.columnCount()
        top_l = self.index(row, FROZEN_COLS + SUB_COLS - 1)
        bot_r = self.index(row, n - 1)
        self.dataChanged.emit(top_l, bot_r, [Qt.DisplayRole, Qt.ForegroundRole, Qt.BackgroundRole])

    def flags(self, index):
        if not index.isValid():
            return Qt.NoItemFlags
        col = index.column()
        if col < FROZEN_COLS:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        subj, si, sub_col = self._subject_for_col(col)
        if not subj or sub_col >= 3:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    def sort(self, column, order=Qt.AscendingOrder):
        if column < FROZEN_COLS:
            key_fn = lambda stu: {0: stu.get("code", ""), 1: stu.get("nombre", ""), 2: stu.get("course", "")}[column]
        else:
            subj, si, sub_col = self._subject_for_col(column)
            if not subj:
                key_fn = lambda stu: ""
            elif sub_col < 3:
                key_fn = lambda stu: self._grades.get(stu["id"], {}).get(subj["id"]) or -1
            else:
                key_fn = lambda stu: self._student_avg(stu["id"]) or -1

        reverse = order == Qt.DescendingOrder
        self.beginResetModel()
        self._students.sort(key=key_fn, reverse=reverse)
        self.endResetModel()

    def get_column_averages(self):
        result = {}
        for si, subj in enumerate(self._subjects):
            avg = self._subject_avg(subj["id"])
            result[si] = avg
        return result

    def _col_for_subject(self, subject_id):
        for si, sub in enumerate(self._subjects):
            if sub["id"] == subject_id:
                return FROZEN_COLS + si * SUB_COLS
        return None

    def _row_for_student(self, student_id):
        for ri, s in enumerate(self._students):
            if s["id"] == student_id:
                return ri
        return None

    def update_grade(self, student_id, subject_id, score):
        if student_id in self._grades and subject_id in self._grades[student_id]:
            self._grades[student_id][subject_id] = score
            row = self._row_for_student(student_id)
            col = self._col_for_subject(subject_id)
            if row is not None and col is not None:
                idx = self.index(row, col)
                self.dataChanged.emit(idx, idx)
                self._update_averages(row)
