# Arquitectura Workbook v1 — Estado: CANDIDATA A CERRADA

**Fecha de creación:** 2026-06-30
**Responsable:** [Tu nombre]

---

## 🔒 Estado Actual
**CANDIDATA A CERRADA** — Pendiente de validación en la aplicación real.

> ⚠️ **No cerrar hasta que se cumplan los criterios de Nivel 1 (Funcional) y Nivel 2 (Fidelidad) en la aplicación real.**

---

## 📋 Principios Arquitectónicos (Inviolables)

| Principio | Descripción | Cumplimiento Actual |
|---|---|---|
| **Workbook JSON única fuente de verdad** | No existe segunda representación editable. El Workbook JSON es el único estado persistente. | ✅ Implementado |
| **Luckysheet único motor de cálculo** | Todas las fórmulas se ejecutan en Luckysheet (headless). No hay motor alternativo. | ✅ Implementado |
| **Fórmulas solo en Meta Editor** | En modo operación, nunca se muestran, editan, crean o eliminan fórmulas. | ✅ Implementado |
| **Usuario solo introduce datos** | El usuario solo edita celdas desbloqueadas (`locked=false`). | ✅ Implementado |
| **AutoSave automático** | Cada modificación se guarda automáticamente en SQLite. | ✅ Implementado |
| **Renderer solo presenta** | El renderer (QTableView) no modifica el Workbook. Solo refleja su estado. | ✅ Implementado |
| **Área activa definida** | El renderer respeta el `active_area` definido en el Workbook. | ✅ Implementado |

---

## 🧪 Criterios de Aceptación

### Nivel 1 — Funcional (Obligatorio)

| Criterio | Validación | Estado |
|---|---|---|
| **Editar celda editable** | El usuario puede editar celdas con `locked=false`. | ✅ |
| **Recalcular fórmulas dependientes** | Al editar una celda, todas las fórmulas dependientes se recalculan automáticamente. | ✅ |
| **Actualizar vista inmediatamente** | La vista se actualiza en tiempo real tras cada edición. | ✅ |
| **AutoSave** | Cada edición se guarda automáticamente en `custom_sections.workbook_json` y `document_versions`. | ✅ |
| **Persistencia** | Al cerrar y reabrir la aplicación, los datos persisten. | ✅ |
| **Meta Editor carga exacto Workbook** | Al abrir el Meta Editor, se carga exactamente el mismo Workbook (con datos y resultados actuales). | ✅ |

### Nivel 2 — Fidelidad

| Criterio | Validación | Estado |
|---|---|---|
| **Anchos de columna** | El renderer respeta `config.columnlen`. | ✅ |
| **Altos de fila** | El renderer respeta `config.rowlen`. | ✅ |
| **Merges** | Las celdas combinadas se muestran correctamente. | ✅ |
| **Bordes** | Los bordes definidos en `bd` se renderizan. | ✅ |
| **Colores y formatos** | Los colores (`bg`, `fc`) y formatos (`it`, `fs`, `ff`) se aplican. | ✅ |
| **Área activa** | Solo se muestra el área definida en `config.active_area`. | ✅ |

### Nivel 3 — Robustez

| Criterio | Validación | Estado |
|---|---|---|
| **Suite de tests pasa** | Todos los tests en `tests/test_workbook_engine.py` pasan. | ✅ |
| **Plantilla de validación** | La plantilla `tests/validation_template.json` se renderiza y calcula correctamente. | ⚠️ Pendiente |
| **Sin regresiones** | Futuras modificaciones no rompen el comportamiento validado. | ⚠️ Pendiente |

---

## 🚫 Cambios Prohibidos

A partir de este punto, **quedan prohibidos los siguientes cambios** sin revisión arquitectónica:

1. **Segundo motor de fórmulas** — No se puede implementar un motor alternativo a Luckysheet.
2. **Segundo modelo editable** — No se puede crear una representación editable del Workbook fuera del JSON.
3. **Duplicar el Workbook** — No se puede mantener una copia sincronizada del Workbook en memoria.
4. **Reemplazar Luckysheet** — No se puede eliminar Luckysheet como motor de cálculo.
5. **Modificar el renderer** — No se puede alterar el renderer para que modifique el Workbook.

---

## ✅ Cambios Permitidos

1. **Corrección de errores** — Bugfixes en el flujo actual.
2. **Optimización** — Mejoras de rendimiento que no alteren el comportamiento.
3. **Nuevas funcionalidades compatibles** — Extensiones que respeten los principios arquitectónicos (ej: nuevos formatos de exportación, integración con otros módulos).

---

## 📝 Validación Oficial

Para cerrar la arquitectura, se debe:

1. **Ejecutar la suite de tests** y confirmar que todas pasan.
2. **Probar la plantilla de validación** en la aplicación real:
   - Importar `tests/validation_template.json` en una sección.
   - Verificar que se renderiza correctamente (Nivel 2).
   - Editar celdas y confirmar que las fórmulas se recalculan (Nivel 1).
   - Cerrar y reabrir la aplicación para validar persistencia.
   - Abrir el Meta Editor y confirmar que carga el Workbook exacto.
3. **Firmar el cierre** actualizando este documento:
   ```markdown
   **Estado:** CERRADA
   **Fecha de cierre:** [AAAA-MM-DD]
   **Responsable de cierre:** [Nombre]
   ```

---

## 🔄 Proceso de Cambio Controlado

Si en el futuro se requiere un cambio que viole los principios arquitectónicos:

1. **Crear una propuesta** en un issue de GitHub.
2. **Revisión arquitectónica** con el equipo.
3. **Actualizar este documento** si el cambio es aprobado.
4. **Validar nuevamente** todos los criterios de aceptación.

---

## 📎 Plantilla de Validación

La plantilla oficial de validación se encuentra en:

```
/home/rohdinn/EduSuite/tests/validation_template.json
```

Esta plantilla **nunca debe modificarse** y servirá como estándar para futuras validaciones.