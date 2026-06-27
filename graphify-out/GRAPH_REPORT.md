# GRAPH_REPORT: EduSuite

## Summary
- Nodes: 568
- Edges: 1865
- Communities: 15
- Total files analyzed: 25 source files

## God Nodes (highest centrality)

- **_()** — centrality=0.243, type=code
- **database.py** — centrality=0.183, type=code
- **Database** — centrality=0.139, type=code
- **._connect()** — centrality=0.125, type=code
- **settings_view.py** — centrality=0.065, type=code
- **r()** — centrality=0.063, type=code
- **e()** — centrality=0.06, type=code
- **N()** — centrality=0.06, type=code
- **Input** — centrality=0.058, type=code
- **SettingsView** — centrality=0.056, type=code

## Communities

### Community 0: Views (248 nodes)

- `views_subjects_view_subjectsview_delete_subject` (._delete_subject())
- `views_main_window_navbutton` (NavButton)
- `views_enrollment_view_enrollmentview_export_debtors` (._export_debtors())
- `schema_users` (Users Table Schema)
- `db_database_delete_grade` (delete_grade())
- `views_enrollment_view_enrollmentview_seed_students` (._seed_students())
- `views_backup_view_backupview_refresh` (.refresh())
- `db_database_row_to_dict` (row_to_dict())
- ... and 240 more

### Community 1: Assets (137 nodes)

- `js_plugin_hn` (hn())
- `js_plugin_cs` (cs())
- `js_plugin_we` (we())
- `js_plugin_i` (I())
- `js_plugin` (_())
- `js_plugin_ye` (ye())
- `js_plugin_xs` (xs())
- `js_plugin_qe` (qe())
- ... and 129 more

### Community 2: Db (79 nodes)

- `db_database_database_get_all_subjects` (.get_all_subjects())
- `db_database_database_create_all_tables` (._create_all_tables())
- `db_database_database_create_students_table` (._create_students_table())
- `db_database_database_delete_teacher` (.delete_teacher())
- `db_database_database_calc_enrollment_status` (._calc_enrollment_status())
- `db_database_database_save_teacher` (.save_teacher())
- `db_database_database_delete_grade` (.delete_grade())
- `db_database_database_save_workbook` (.save_workbook())
- ... and 71 more

### Community 3: Views (39 nodes)

- `views_settings_view_settingsview_build` (._build())
- `views_settings_view_accent_btn` (_accent_btn())
- `views_settings_view_settingsview_load_users` (._load_users())
- `views_settings_view_settingsview_refresh` (.refresh())
- `views_settings_view_settingsview_build_roles` (._build_roles())
- `views_settings_view_settingsview_init` (.__init__())
- `db_database_delete_user` (delete_user())
- `qcombobox` (QComboBox)
- ... and 31 more

### Community 4: Views (24 nodes)

- `views_editor_view_handler_do_get` (.do_GET())
- `views_editor_view_editorview` (EditorView)
- `views_editor_view_editorview_on_level_change` (._on_level_change())
- `views_editor_view_handler` (_Handler)
- `assets_luckysheet_pluginjs` (LuckySheetPluginJS)
- `views_editor_view_editorview_find_port` (._find_port())
- `views_editor_view_handler_log_message` (.log_message())
- `views_editor_view_editorview_check_save` (._check_save())
- ... and 16 more

### Community 5: Backup (12 nodes)

- `datetime` (datetime)
- `backup_backup_manager_list_backups` (list_backups())
- `backup_backup_manager_restore_from_backup` (restore_from_backup())
- `views_dashboard_view_statblock_set_value` (.set_value())
- `views_backup_view_backupview_local_backup` (._local_backup())
- `db_database_get_db_path` (get_db_path())
- `views_dashboard_view_dashboardview_refresh` (.refresh())
- `db_database_get_stats` (get_stats())
- ... and 4 more

### Community 6: Views (8 nodes)

- `views_main_window_mainwindow_navigate` (._navigate())
- `views_main_window_navbutton_update_style` (._update_style())
- `views_main_window_navbutton_set_active` (.set_active())
- `views_main_window_sidebarsection_init` (.__init__())
- `views_main_window_mainwindow_init` (.__init__())
- `views_main_window_mainwindow_show_first_available` (._show_first_available())
- `views_main_window_navbutton_init` (.__init__())
- `views_main_window_mainwindow_init_views` (._init_views())

### Community 7: Ui Style.Py (7 nodes)

- `ui_style_combo_init` (.__init__())
- `ui_style_table_init` (.__init__())
- `ui_style_panel_init` (.__init__())
- `ui_style_input_init` (.__init__())
- `ui_style_separator_init` (.__init__())
- `ui_style_header_init` (.__init__())
- `ui_style_button_init` (.__init__())

### Community 8: Assets (3 nodes)

- `editor_http_server` (Local HTTP Server Editor)
- `assets_luckysheet_standalone` (Luckysheet Standalone HTML)
- `assets_luckysheet_index` (Luckysheet QWebChannel HTML)

### Community 9: Views (3 nodes)

- `views_teachers_view_crud_pattern` (TeacherCRUDPattern)
- `views_students_view_crud_pattern` (StudentCRUDPattern)
- `views_subjects_view_crud_pattern` (SubjectCRUDPattern)

### Community 10: Pyside6 (3 nodes)

- `pyqt5` (pyqt5)
- `pyside6_init` (__init__.py)
- `sys` (sys)

### Community 11: Pyside6 (2 nodes)

- `pyside6_pyqt5_shim` (PySide6 to PyQt5 Shim Pattern)
- `pyside6___init__` (PySide6/PyQt5 Compatibility Shim)

### Community 12: .Anchor-Summary.Md (1 nodes)

- `anchor_summary_md` (Project Summary Document)

### Community 13: Requirements.Txt (1 nodes)

- `requirements` (Python Dependencies)

### Community 14: .Anchor-Summary.Md (1 nodes)

- `edusuite` (EduSuite)

## Surprising Connections

- **backup_manager.py** `imports` **os** (community 5 → 0)
- **backup_manager.py** `calls` **database.py** (community 5 → 0)
- **database.py** `contains` **Database** (community 0 → 2)
- **database.py** `contains` **get_connection()** (community 0 → 4)
- **database.py** `contains` **get_db_path()** (community 0 → 5)
- **database.py** `contains` **get_subjects_by_level()** (community 0 → 4)
- **database.py** `contains` **get_stats()** (community 0 → 5)
- **database.py** `contains` **get_all_roles()** (community 0 → 3)
- **database.py** `contains` **delete_role()** (community 0 → 3)
- **database.py** `contains` **get_all_users()** (community 0 → 3)

## Suggested Questions

- How does the permission system control access across all views?
- What is the architecture of the embedded spreadsheet editor and how does it connect to the database?
- How does the enrollment/payment system track students across school years?
- What design system patterns define the UI (colors, typography, spacing)?
- How are students imported from Excel and synchronized with the database?
