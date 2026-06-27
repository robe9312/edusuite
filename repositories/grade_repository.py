from db.database import (
    get_grade, upsert_grade, delete_grade,
    get_students_by_course, get_subjects_for_course,
    get_subjects_by_group, get_distinct_courses,
    get_all_students,
)
from core.cache import CacheManager
from core.event_bus import EventBus


class BaseRepository:
    def __init__(self):
        self.cache = CacheManager()
        self.bus = EventBus()


class GradeRepository(BaseRepository):
    def get_grade(self, student_id, subject_id, period):
        cache_key = f"grade:{student_id}:{subject_id}:{period}"
        cached = self.cache.grades.get(cache_key)
        if cached is not None:
            return cached
        result = get_grade(student_id, subject_id, period)
        self.cache.grades.set(cache_key, result)
        return result

    def set_grade(self, student_id, subject_id, period, score):
        upsert_grade(student_id, subject_id, period, score)
        cache_key = f"grade:{student_id}:{subject_id}:{period}"
        self.cache.grades.set(cache_key, {"score": score})
        self.cache.grades.invalidate()
        self.bus.emit_grade_updated(student_id, subject_id, period, score)


class SubjectRepository(BaseRepository):
    def for_course(self, course):
        cached = self.cache.subjects.get(course)
        if cached is not None:
            return cached
        subjects = get_subjects_for_course(course)
        if not subjects:
            from config import COURSE_TO_LEVEL
            level = COURSE_TO_LEVEL.get(course)
            if level:
                subjects = get_subjects_by_group(level)
        self.cache.subjects.set(course, subjects)
        return subjects


class StudentRepository(BaseRepository):
    def by_course(self, course):
        cached = self.cache.students.get(f"course:{course}")
        if cached is not None:
            return cached
        students = get_students_by_course(course)
        self.cache.students.set(f"course:{course}", students)
        return students

    def all(self):
        cached = self.cache.students.get("all")
        if cached is not None:
            return cached
        students = get_all_students()
        self.cache.students.set("all", students)
        return students


class CourseRepository(BaseRepository):
    def all_distinct(self):
        cached = self.cache.courses.get("all")
        if cached is not None:
            return cached
        courses = get_distinct_courses()
        self.cache.courses.set("all", courses)
        return courses


grade_repo = GradeRepository()
subject_repo = SubjectRepository()
student_repo = StudentRepository()
course_repo = CourseRepository()
