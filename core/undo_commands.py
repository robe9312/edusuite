from PySide6.QtGui import QUndoCommand


class SetGradeCommand(QUndoCommand):
    def __init__(self, student_id, subject_id, period, new_score, old_score=None, model=None, repo=None):
        super().__init__()
        self._student_id = student_id
        self._subject_id = subject_id
        self._period = period
        self._new_score = new_score
        self._old_score = old_score
        self._model = model
        self._repo = repo
        self.setText(f"Nota {subject_id} {period}")

    def redo(self):
        if self._model:
            self._model._grades[self._student_id][self._subject_id] = self._new_score
            col = self._model._col_for_subject(self._subject_id)
            if col is not None:
                row = self._model._row_for_student(self._student_id)
                if row is not None:
                    idx = self._model.index(row, col)
                    self._model.dataChanged.emit(idx, idx)
                    self._model._update_averages(row)
            self._model._mark_dirty(self._student_id, self._subject_id)
        elif self._repo:
            self._repo.set_grade(self._student_id, self._subject_id, self._period, self._new_score)

    def undo(self):
        if self._model:
            self._model._grades[self._student_id][self._subject_id] = self._old_score
            col = self._model._col_for_subject(self._subject_id)
            if col is not None:
                row = self._model._row_for_student(self._student_id)
                if row is not None:
                    idx = self._model.index(row, col)
                    self._model.dataChanged.emit(idx, idx)
                    self._model._update_averages(row)
            self._model._mark_dirty(self._student_id, self._subject_id)
        elif self._old_score is not None and self._repo:
            self._repo.set_grade(self._student_id, self._subject_id, self._period, self._old_score)


class SetCellCommand(QUndoCommand):
    def __init__(self, col_id, row_id, new_value, old_value=None, model=None, repo=None):
        super().__init__()
        self._col_id = col_id
        self._row_id = row_id
        self._new_value = new_value
        self._old_value = old_value
        self._model = model
        self._repo = repo
        self.setText(f"Celda {col_id}")

    def redo(self):
        if self._model:
            self._model._data.setdefault(self._row_id, {})[self._col_id] = self._new_value
            self._model._mark_dirty(self._row_id, self._col_id)

    def undo(self):
        if self._model:
            if self._old_value is not None:
                self._model._data.setdefault(self._row_id, {})[self._col_id] = self._old_value
            else:
                self._model._data.get(self._row_id, {}).pop(self._col_id, None)
            self._model._mark_dirty(self._row_id, self._col_id)
