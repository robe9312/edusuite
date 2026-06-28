from __future__ import annotations
from typing import Any, Dict, List, Optional


class StatisticsService:
    def __init__(self):
        self._cache = {}

    def dashboard_data(self) -> dict:
        from db.database import get_dashboard_extended, get_recent_activity
        data = get_dashboard_extended()
        data["activity"] = get_recent_activity(8)
        return data

    def course_distribution(self) -> List[dict]:
        from db.database import get_stats_by_curso
        return get_stats_by_curso()

    def distinct_courses(self) -> List[str]:
        from db.database import get_distinct_courses
        return get_distinct_courses()

    def system_stats(self) -> dict:
        from db.database import get_stats
        return get_stats()

    def document_summary(self) -> dict:
        from db.database import get_all_custom_sections
        sections = get_all_custom_sections()
        return {
            "total": len(sections),
            "workbooks": sum(1 for s in sections if s.get("workbook_json")),
            "simple": sum(1 for s in sections if not s.get("workbook_json")),
            "recent": sections[-5:] if sections else [],
        }
