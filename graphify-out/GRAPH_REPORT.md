# Graph Report - EduSuite  (2026-06-27)

## Corpus Check
- 54 files · ~106,153 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1099 nodes · 3511 edges · 49 communities (39 shown, 10 thin omitted)
- Extraction: 83% EXTRACTED · 17% INFERRED · 0% AMBIGUOUS · INFERRED: 603 edges (avg confidence: 0.66)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `d415d4aa`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]

## God Nodes (most connected - your core abstractions)
1. `_()` - 246 edges
2. `_()` - 138 edges
3. `Database` - 90 edges
4. `_l()` - 47 edges
5. `gy()` - 44 edges
6. `r()` - 40 edges
7. `Ey()` - 39 edges
8. `e()` - 37 edges
9. `Input` - 37 edges
10. `MainWindow` - 37 edges

## Surprising Connections (you probably didn't know these)
- `ExportDialog` --uses--> `ClipboardEngine`  [INFERRED]
  views/grades_view.py → core/clipboard_engine.py
- `StatBadge` --uses--> `ClipboardEngine`  [INFERRED]
  views/grades_view.py → core/clipboard_engine.py
- `GradeTableModel` --uses--> `SetGradeCommand`  [INFERRED]
  models/grade_model.py → core/undo_commands.py
- `SpreadsheetTableModel` --uses--> `SetCellCommand`  [INFERRED]
  models/spreadsheet_model.py → core/undo_commands.py
- `ExportDialog` --uses--> `ColumnType`  [INFERRED]
  views/grades_view.py → models/column_definition.py

## Import Cycles
- None detected.

## Communities (49 total, 10 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.13
Nodes (10): create_school_year(), get_school_year(), seed_enrollment_for_year(), set_active_school_year(), upsert_enrollment(), EnrollmentView, EnrollmentExportToExcel, PaymentDialog (+2 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (139): _(), a(), ae(), an(), as(), at(), B(), be() (+131 more)

### Community 3 - "Community 3"
Cohesion: 0.09
Nodes (21): delete_role(), delete_user(), get_all_roles(), get_all_school_years(), get_all_users(), update_school_year(), QComboBox, QTableWidget (+13 more)

### Community 4 - "Community 4"
Cohesion: 0.11
Nodes (12): get_connection(), get_distinct_courses(), get_enrollments_by_year(), get_subjects_by_level(), http_server, os, pyqt5_qtwebenginewidgets, pyside6_qtwebenginewidgets (+4 more)

### Community 5 - "Community 5"
Cohesion: 0.43
Nodes (6): list_backups(), local_backup(), restore_from_backup(), datetime, get_db_path(), shutil

### Community 6 - "Community 6"
Cohesion: 0.05
Nodes (17): authenticate(), get_role_permissions(), QMainWindow, QPushButton, current_user(), has_permission(), login(), logout() (+9 more)

### Community 7 - "Community 7"
Cohesion: 0.24
Nodes (6): deactivate_student(), _map_student_data(), Traduce keys English → Spanish si es necesario., Traduce keys English → Spanish si es necesario., search_students(), update_student()

### Community 8 - "Community 8"
Cohesion: 1.00
Nodes (3): Luckysheet QWebChannel HTML, Luckysheet Standalone HTML, Local HTTP Server Editor

### Community 9 - "Community 9"
Cohesion: 0.20
Nodes (9): delete_teacher(), get_all_teachers(), get_teacher(), save_teacher(), teacher_code_exists(), update_teacher(), Table, TeacherDialog (+1 more)

### Community 15 - "Community 15"
Cohesion: 0.07
Nodes (43): _(), a(), Aa(), Al(), as(), Bo(), Ch(), co() (+35 more)

### Community 16 - "Community 16"
Cohesion: 0.15
Nodes (30): ba(), bh(), cd(), Cl(), Cs(), Da(), dd(), fh() (+22 more)

### Community 17 - "Community 17"
Cohesion: 0.17
Nodes (16): am(), Ca(), es(), fo(), jo(), Ko(), lo(), No() (+8 more)

### Community 18 - "Community 18"
Cohesion: 0.06
Nodes (19): contextlib, get_enrollment(), EduSuite — db/database.py SQLite puro con clase Database + wrappers module-level, save_role(), save_user(), set_role_permissions(), update_role(), update_user() (+11 more)

### Community 19 - "Community 19"
Cohesion: 0.14
Nodes (13): init_db(), 0-10 Grading Scale T1/T2/T3, main(), Open Design Dark Theme, pyside6_qtcore, pyside6_qtgui, pyside6_qtwidgets, apply_global_style() (+5 more)

### Community 21 - "Community 21"
Cohesion: 0.12
Nodes (11): cached(), CacheManager, TTLCache, EventBus, delete_grade(), QObject, BaseRepository, CourseRepository (+3 more)

### Community 22 - "Community 22"
Cohesion: 0.12
Nodes (25): get_debtors(), get_grade(), get_grades_by_student(), get_report_by_course(), get_report_by_student(), get_student(), get_students_by_course(), get_subjects_by_group() (+17 more)

### Community 23 - "Community 23"
Cohesion: 0.11
Nodes (12): get_stats(), QFrame, QLabel, Header, Panel, Separator, BackupView, DashboardView (+4 more)

### Community 24 - "Community 24"
Cohesion: 0.14
Nodes (24): bd(), Bm(), cu(), Do(), du(), Fm(), fu(), gn() (+16 more)

### Community 25 - "Community 25"
Cohesion: 0.22
Nodes (22): Ac(), Ay(), bc(), c(), cm(), dc(), Ec(), ed() (+14 more)

### Community 27 - "Community 27"
Cohesion: 0.22
Nodes (6): delete_subject(), save_subject(), update_subject(), Combo, SubjectDialog, SubjectsView

### Community 28 - "Community 28"
Cohesion: 0.13
Nodes (28): bu(), Cc(), Cy(), dm(), em(), Ey(), Fs(), hm() (+20 more)

### Community 29 - "Community 29"
Cohesion: 0.15
Nodes (11): apply_import(), diff_import(), get_all_students(), get_all_subjects(), get_student_by_code(), get_subject(), apply_import_result(), get_subject_by_name() (+3 more)

### Community 30 - "Community 30"
Cohesion: 0.12
Nodes (21): ad(), ah(), ds(), eh(), hh(), hs(), ih(), ku() (+13 more)

### Community 31 - "Community 31"
Cohesion: 0.26
Nodes (5): build_grade_columns(), ColumnDef, ColumnType, TemplateManager, sqlite3

### Community 32 - "Community 32"
Cohesion: 0.07
Nodes (8): ClipboardEngine, upsert_grade(), GradeProxyModel, QSortFilterProxyModel, GradesExportToExcel, GradeMatrixPattern, GradesView, SpreadsheetView

### Community 33 - "Community 33"
Cohesion: 0.24
Nodes (12): json, pathlib, _ensure(), get(), get_all(), reset(), _save(), set_many() (+4 more)

### Community 34 - "Community 34"
Cohesion: 0.19
Nodes (17): ai(), ci(), ei(), Fi(), hi(), _i(), ii(), Jl() (+9 more)

### Community 35 - "Community 35"
Cohesion: 0.18
Nodes (10): Blocked, Constraints & Preferences, Critical Context, Done, Goal, In Progress, Key Decisions, Next Steps (+2 more)

### Community 36 - "Community 36"
Cohesion: 0.18
Nodes (10): delete_expense(), get_active_school_year(), get_all_expenses(), get_enrollment_stats(), get_expense(), save_expense(), update_expense(), QWidget (+2 more)

### Community 37 - "Community 37"
Cohesion: 0.18
Nodes (10): save_student(), student_code_exists(), QLineEdit, Input, StatsRefreshProtocol, StudentCRUDPattern, StudentDialog, StudentsView (+2 more)

### Community 39 - "Community 39"
Cohesion: 0.24
Nodes (3): SetCellCommand, SetGradeCommand, QUndoCommand

### Community 40 - "Community 40"
Cohesion: 0.33
Nodes (9): dh(), Gd(), gh(), Il(), kh(), mh(), ph(), wo() (+1 more)

### Community 42 - "Community 42"
Cohesion: 0.32
Nodes (4): LuckySheetPluginJS, BaseHTTPRequestHandler, _Handler, LuckySheetIntegration

### Community 45 - "Community 45"
Cohesion: 0.40
Nodes (3): heatmap_color(), heatmap_text_color(), lerp_color()

### Community 46 - "Community 46"
Cohesion: 0.17
Nodes (4): QDialog, ExportDialog, StatBadge, StudentPanel

## Knowledge Gaps
- **9 isolated node(s):** `Goal`, `Constraints & Preferences`, `Done`, `In Progress`, `Blocked` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Database` connect `Community 2` to `Community 38`, `Community 43`, `Community 48`, `Community 18`, `Community 22`, `Community 29`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._
- **Why does `_()` connect `Community 15` to `Community 1`, `Community 34`, `Community 40`, `Community 16`, `Community 17`, `Community 24`, `Community 25`, `Community 28`, `Community 30`?**
  _High betweenness centrality (0.093) - this node is a cross-community bridge._
- **Why does `SpreadsheetTableModel` connect `Community 26` to `Community 32`, `Community 39`, `Community 46`, `Community 19`, `Community 20`, `Community 31`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Are the 16 inferred relationships involving `_()` (e.g. with `ae()` and `be()`) actually correct?**
  _`_()` has 16 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `gy()` (e.g. with `cm()` and `dh()`) actually correct?**
  _`gy()` has 10 INFERRED edges - model-reasoned connections that need verification._
- **What connects `EduSuite — db/database.py SQLite puro con clase Database + wrappers module-level`, `Traduce keys English → Spanish si es necesario.`, `Export all trimesters for a course — ACTA style per student.` to the rest of the system?**
  _15 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.13227513227513227 - nodes in this community are weakly interconnected._