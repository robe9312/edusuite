from PySide6.QtCore import QObject, Signal


class EventBus(QObject):
    grade_updated = Signal(int, int, str, float)
    student_changed = Signal(int)
    course_changed = Signal(str)
    data_refreshed = Signal()

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            QObject.__init__(cls._instance)
        return cls._instance

    def emit_grade_updated(self, student_id, subject_id, period, score):
        self.grade_updated.emit(student_id, subject_id, period, score)

    def emit_student_changed(self, student_id):
        self.student_changed.emit(student_id)

    def emit_course_changed(self, course):
        self.course_changed.emit(course)

    def emit_data_refreshed(self):
        self.data_refreshed.emit()
