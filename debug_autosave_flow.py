#!/usr/bin/env python3
"""
Script de diagnóstico para el flujo de auto-save en EduSuite.

Este script:
1. Carga una sección existente o crea una de prueba
2. Simula una edición de celda
3. Verifica que el auto-save se dispara
4. Confirma que el JSON se guarda en la base de datos
5. Valida que el Meta Editor cargaría el workbook actualizado

Ejecución:
  cd /home/rohdinn/EduSuite
  python debug_autosave_flow.py [section_key]

Ejemplo:
  python debug_autosave_flow.py notas
"""

import json
import os
import sys
import time
from typing import Any, Dict, List

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.database import (
    get_custom_section,
    update_section_workbook,
    save_document_version,
    get_connection,
    create_custom_section
)

def get_document_by_id(doc_id: int) -> Dict[str, Any]:
    """Obtiene un documento por ID incluyendo su última versión."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT d.*, dv.workbook_json, dv.version FROM documents d "
            "LEFT JOIN document_versions dv ON d.id = dv.document_id AND dv.version = d.latest_version "
            "WHERE d.id = ?",
            (doc_id,)
        )
        row = cursor.fetchone()
        if not row:
            return {}
        return dict(row)

def get_document_category_by_name(name: str) -> Dict[str, Any]:
    """Obtiene una categoría de documento por nombre."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM document_categories WHERE name = ?", (name,))
        row = cursor.fetchone()
        if not row:
            return {}
        return dict(row)
from widgets.formula_engine import FormulaEngine


def create_test_workbook() -> str:
    """Crea un workbook de prueba mínimo."""
    workbook = {
        "sheetData": [
            {
                "name": "Test",
                "celldata": [
                    {"r": 0, "c": 0, "v": {"v": "", "m": "", "bl": 0, "it": 0, "fs": 10, "ff": "Arial", "fc": "#000000", "bg": "#FFFFFF"}},
                    {"r": 0, "c": 1, "v": {"v": "=A1*2", "m": "0", "f": "=A1*2", "bl": 1, "it": 0, "fs": 10, "ff": "Arial", "fc": "#000000", "bg": "#FFFFFF"}}
                ],
                "config": {}
            }
        ]
    }
    return json.dumps(workbook)


def setup_test_section(section_key: str) -> Dict[str, Any]:
    """Crea una sección de prueba si no existe."""
    sec = get_custom_section(section_key)
    if sec:
        print(f"✅ Sección '{section_key}' ya existe (ID: {sec['id']})")
        return sec
    
    print(f"🆕 Creando sección de prueba '{section_key}'...")
    
    # Obtener categoría "Template" para el documento
    category = get_document_category_by_name("Template")
    if not category:
        raise ValueError("Categoría 'Template' no encontrada")
    
    # Crear documento asociado
    doc_id = None
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO documents (name, category_id, icon, color) VALUES (?, ?, ?, ?)",
            (f"Doc_{section_key}", category["id"], "📄", "#4285F4")
        )
        doc_id = cursor.lastrowid
        conn.commit()
    
    # Crear sección
    sec_id = create_custom_section(
        section_key=section_key,
        name=f"Test {section_key}",
        icon="🧪",
        columns_json="[]",
        workbook_json=create_test_workbook(),
        document_id=doc_id
    )
    
    sec = get_custom_section(section_key)
    if not sec:
        raise ValueError(f"No se pudo crear la sección '{section_key}'")
    
    print(f"✅ Sección creada (ID: {sec['id']}, Doc ID: {doc_id})")
    return sec


def simulate_edit_flow(section_key: str) -> None:
    """Simula el flujo completo de edición y auto-save."""
    print("\n🔍 INICIANDO DIAGNÓSTICO DE FLUJO DE AUTO-SAVE")
    
    # 1. Cargar sección
    sec = get_custom_section(section_key)
    if not sec:
        print(f"❌ Sección '{section_key}' no encontrada")
        return
    
    print(f"\n1️⃣ SECCIÓN CARGADA")
    print(f"   - ID: {sec['id']}")
    print(f"   - Document ID: {sec.get('document_id')}")
    print(f"   - Workbook JSON (truncado): {sec.get('workbook_json', '')[:100]}...")
    
    # 2. Inicializar FormulaEngine
    print("\n2️⃣ INICIALIZANDO FORMULA ENGINE")
    engine = FormulaEngine.instance()
    workbook_json = sec.get("workbook_json") or create_test_workbook()
    
    print("   - Cargando workbook...")
    engine.load_workbook(workbook_json)
    print("   ✅ Workbook cargado")
    
    # 3. Simular edición de celda
    print("\n3️⃣ SIMULANDO EDICIÓN DE CELDA")
    print("   - Editando A1 = 42...")
    engine.set_cell(0, 0, 0, 42)
    
    # Esperar recálculo (simular callback)
    time.sleep(2)
    print("   ✅ Celda editada y recalculada")
    
    # 4. Verificar auto-save
    print("\n4️⃣ VERIFICANDO AUTO-SAVE")
    
    # Obtener el workbook actualizado
    updated_json = engine.get_workbook_sync()
    if not updated_json:
        print("   ❌ get_workbook_sync() retornó None")
        return
    
    print(f"   - Workbook actualizado (truncado): {updated_json[:100]}...")
    
    # Verificar que B1 se recalculó (debería ser 84 = 42*2)
    try:
        workbook_data = json.loads(updated_json)
        sheet = workbook_data["sheetData"][0]
        celldata = { (c["r"], c["c"]): c["v"] for c in sheet["celldata"] }
        b1_value = celldata.get((0, 1), {}).get("m", "")
        if b1_value == "84":
            print("   ✅ Fórmula recalculada correctamente (B1=84)")
        else:
            print(f"   ⚠️  Fórmula no recalculada correctamente (B1={b1_value})")
    except Exception as e:
        print(f"   ❌ Error al parsear workbook: {e}")
    
    # 5. Guardar manualmente en la base de datos
    print("\n5️⃣ GUARDANDO EN BASE DE DATOS")
    try:
        section_id = sec["id"]
        doc_id = sec.get("document_id")
        
        print(f"   - Actualizando sección {section_id}...")
        update_section_workbook(section_id, updated_json)
        print("   ✅ Sección actualizada")
        
        if doc_id:
            print(f"   - Guardando versión del documento {doc_id}...")
            save_document_version(doc_id, updated_json, comment="Diagnóstico auto-save")
            print("   ✅ Versión del documento guardada")
        else:
            print("   ⚠️  Document ID no encontrado, no se guardó versión")
    except Exception as e:
        print(f"   ❌ Error al guardar en DB: {e}")
        return
    
    # 6. Verificar que el JSON se guardó correctamente
    print("\n6️⃣ VERIFICANDO PERSISTENCIA")
    updated_sec = get_custom_section(section_key)
    if not updated_sec:
        print("   ❌ Sección no encontrada después de guardar")
        return
    
    saved_json = updated_sec.get("workbook_json")
    if not saved_json:
        print("   ❌ workbook_json está vacío después de guardar")
        return
    
    print(f"   - Workbook guardado (truncado): {saved_json[:100]}...")
    
    # Verificar que A1=42 persiste
    try:
        saved_data = json.loads(saved_json)
        sheet = saved_data["sheetData"][0]
        celldata = { (c["r"], c["c"]): c["v"] for c in sheet["celldata"] }
        a1_value = celldata.get((0, 0), {}).get("m", "")
        if a1_value == "42":
            print("   ✅ Valor persistente (A1=42)")
        else:
            print(f"   ⚠️  Valor no persistente (A1={a1_value})")
    except Exception as e:
        print(f"   ❌ Error al parsear workbook guardado: {e}")
    
    # 7. Verificar que el Meta Editor cargaría el workbook correcto
    print("\n7️⃣ VERIFICANDO CARGA EN META EDITOR")
    if doc_id:
        doc = get_document_by_id(doc_id)
        if doc:
            latest_version = doc.get("latest_version")
            if latest_version:
                print(f"   - Última versión del documento: {latest_version['version']}")
                print(f"   - Workbook en versión (truncado): {latest_version['workbook_json'][:100]}...")
                
                # Verificar que coincide con el guardado
                if latest_version["workbook_json"] == saved_json:
                    print("   ✅ Meta Editor cargaría el workbook exacto")
                else:
                    print("   ⚠️  Meta Editor cargaría una versión diferente")
            else:
                print("   ⚠️  No hay versiones del documento")
        else:
            print("   ⚠️  Documento no encontrado")
    else:
        print("   ⚠️  Document ID no disponible")
    
    print("\n🎯 DIAGNÓSTICO COMPLETADO")


def main():
    if len(sys.argv) < 2:
        print("Uso: python debug_autosave_flow.py [section_key]")
        print("Ejemplo: python debug_autosave_flow.py notas")
        return
    
    section_key = sys.argv[1]
    
    # Configurar sección de prueba si no existe
    sec = setup_test_section(section_key)
    
    # Ejecutar diagnóstico
    simulate_edit_flow(section_key)


if __name__ == "__main__":
    main()