# EduSuite

Motor de formularios/plantillas basado en Excel. Cada sección del sidebar es una plantilla Luckysheet renderizada fielmente en Qt.

## Arquitectura

```
┌─────────────────────────────────────────────────────┐
│                   Meta Editor                        │
│               (Luckysheet en QWebEngine)              │
└─────────────────────────┬───────────────────────────┘
                          │ diseño libre
                          ▼
┌─────────────────────────────────────────────────────┐
│                  Workbook JSON                       │
│          (única fuente de verdad)                     │
│    [{name, celldata, config, merge, rowlen, ...}]    │
└─────────────────────────┬───────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              spreadsheet/renderer/                    │
│                                                      │
│  WorkbookRenderer  ──  orquestador                    │
│       │                                              │
│       ▼                                              │
│  SheetRenderer  ──  renderiza UNA hoja               │
│       │                                              │
│       ├── LayoutRenderer    → área activa, tamaños   │
│       ├── StyleRenderer     → fuente, color, bordes  │
│       ├── MergeRenderer     → celdas combinadas      │
│       ├── ReadOnlyPolicy    → locked / editable       │
│       └── WidgetFactory     → editor según tipo       │
│                                                      │
└─────────────────────────┬───────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                  QTableWidget                        │
│          (representación fiel del workbook)           │
└─────────────────────────────────────────────────────┘
```

## Las 12 reglas del motor

1. **La plantilla es la interfaz** — no existe UI hecha en Qt por módulo
2. **La app nunca inventa columnas** — muestra exactamente lo que hay en la plantilla
3. **Solo interpreta tipos de celdas** — texto, número, checkbox, fecha, lista, fórmula
4. **El Área Activa es la pantalla** — solo se renderiza el rectángulo con contenido
5. **Las fórmulas viven en Luckysheet** — la app solo muestra el resultado calculado
6. **Solo ciertas celdas son editables** — según `cell.locked`
7. **El renderer es 100% fiel** — copia colores, bordes, merges, tamaños, alineación, formato
8. **El Workbook es la única fuente de verdad** — sin transformaciones intermedias
9. **Los datos variables sustituyen solo celdas desbloqueadas** — no toca encabezados ni fórmulas
10. **El dominio desaparece** — el renderer no sabe si es Notas, Asistencia o Inventario
11. **La edición siempre vuelve a Luckysheet** — Qt solo consume el resultado
12. **El Workbook define el comportamiento** — metadatos en celdas/rangos definen interacción

## Estructura del proyecto

```
EduSuite/
├── assets/luckysheet/     → Luckysheet standalone + plugins
├── db/database.py         → SQLite: CRUD de secciones, documentos, versiones
├── engine/                 → MetaEngine (componentes dinámicos)
├── logs/                   → Rotación de logs, logger
├── session.py              → Manejo de sesión y permisos
├── spreadsheet/
│   ├── core/               → GridCell, MemoryGrid, CellType
│   ├── datasource/         → MemoryDataSource
│   ├── engine/             → SpreadsheetEngine (legacy)
│   ├── renderer/           ← NUEVO: pipeline de render fiel a Luckysheet
│   │   ├── __init__.py
│   │   ├── workbook_renderer.py
│   │   ├── sheet_renderer.py
│   │   ├── layout_renderer.py
│   │   ├── style_renderer.py
│   │   ├── merge_renderer.py
│   │   ├── readonly_policy.py
│   │   ├── widget_factory.py
│   │   └── render_context.py
│   └── services/           → DocumentService
├── views/
│   ├── main_window.py      → Ventana principal, sidebar, navegación
│   ├── editor_view.py      → Servidor HTTP + handler /save
│   └── ...
├── widgets/
│   ├── sidebar.py          → Sidebar dinámico desde DB
│   ├── workbook_renderer.py → WorkbookRenderView (usa el nuevo renderer)
│   ├── luckysheet_window.py → QMainWindow con QWebEngineView
│   ├── meta_editor.py       → Administración de secciones
│   └── ...
├── main.py                 → Entry point, exception hook, log startup
├── config.py               → Colores, heatmap, constantes
└── tests/                  → Migración de estudiantes, tests unitarios
```

## Flujo de guardado

```
Luckysheet (standalone.html)
    │ cellEdited / autoSave / beforeunload
    │ POST /save  {sheetData: [...]}
    ▼
_Handler.do_POST  (editor_view.py)
    │ update_section_workbook(sid, wb_json)
    │ save_document_version(doc_id, wb_json)
    │ update_section_document_id(sid, doc_id)  ← si no existía
    ▼
SQLite: document_versions.workbook_json
```

## Flujo de renderizado

```
WorkbookRenderView._load_content()
    │ doc_id = section.get("document_id")
    │ workbook_json = DocumentService.latest_workbook(doc_id)
    ▼
WorkbookRenderer.from_json(workbook_json)
    │ itera sheets → SheetRenderer por hoja
    │   LayoutRenderer → área activa, column widths, row heights
    │   StyleRenderer  → display_value + apply_to_item
    │   MergeRenderer  → setSpan
    ▼
QTableWidget (fiel al diseño original)
```