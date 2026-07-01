#!/usr/bin/env python3
"""
Script simplificado para diagnosticar problemas de auto-save.

Ejecución:
  cd /home/rohdinn/EduSuite
  python debug_autosave_simple.py
"""

import json
import os
import sys
from typing import Any, Dict

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db.database import (
    get_custom_section,
    update_section_workbook,
    save_document_version,
    get_connection,
    create_custom_section
)


def test_database_connection():
    """Verifica que la base de datos es accesible."""
    print("🔍 1. Verificando conexión a la base de datos...")
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='custom_sections'")
            if cursor.fetchone():
                print("   ✅ Tabla 'custom_sections' existe")
            else:
                print("   ❌ Tabla 'custom_sections' no encontrada")
                return False
        return True
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        return False


def test_json_serialization():
    """Verifica que el JSON se serializa correctamente."""
    print("\n🔍 2. Verificando serialización JSON...")
    try:
        workbook = {
            "sheetData": [
                {
                    "name": "Test",
                    "celldata": [
                        {"r": 0, "c": 0, "v": {"v": "42", "m": "42", "bl": 0}}
                    ],
                    "config": {}
                }
            ]
        }
        json_str = json.dumps(workbook)
        print(f"   ✅ JSON serializado: {json_str[:100]}...")
        
        # Verificar que se puede deserializar
        parsed = json.loads(json_str)
        if parsed["sheetData"][0]["celldata"][0]["v"]["v"] == "42":
            print("   ✅ JSON deserializado correctamente")
            return True
        else:
            print("   ❌ JSON deserializado incorrectamente")
            return False
    except Exception as e:
        print(f"   ❌ Error de serialización: {e}")
        return False


def test_section_update():
    """Verifica que se puede actualizar una sección."""
    print("\n🔍 3. Verificando actualización de sección...")
    try:
        # Crear una sección de prueba
        section_key = "debug_test"
        
        # Verificar si ya existe
        sec = get_custom_section(section_key)
        if not sec:
            print(f"   ⚠️  Sección '{section_key}' no existe, creando...")
            sec_id = create_custom_section(
                section_key=section_key,
                name="Debug Test",
                icon="🐛",
                columns_json="[]",
                workbook_json='{"sheetData": [{"name": "Test", "celldata": [], "config": {}}]}'
            )
            sec = get_custom_section(section_key)
            if not sec:
                print("   ❌ No se pudo crear la sección")
                return False
        
        section_id = sec["id"]
        print(f"   - Sección ID: {section_id}")
        
        # Crear workbook de prueba
        workbook = {
            "sheetData": [
                {
                    "name": "Test",
                    "celldata": [
                        {"r": 0, "c": 0, "v": {"v": "42", "m": "42", "bl": 0}}
                    ],
                    "config": {}
                }
            ]
        }
        json_str = json.dumps(workbook)
        
        # Actualizar sección
        update_section_workbook(section_id, json_str)
        print("   ✅ Sección actualizada")
        
        # Verificar que se guardó
        updated_sec = get_custom_section(section_key)
        if updated_sec and updated_sec.get("workbook_json") == json_str:
            print("   ✅ Workbook guardado correctamente")
            return True
        else:
            print("   ❌ Workbook no se guardó correctamente")
            return False
    except Exception as e:
        print(f"   ❌ Error al actualizar sección: {e}")
        return False


def test_document_version():
    """Verifica que se puede guardar una versión de documento."""
    print("\n🔍 4. Verificando guardado de versión de documento...")
    try:
        # Obtener una sección con document_id
        sec = get_custom_section("notas")  # Cambia por una sección existente
        if not sec:
            print("   ⚠️  Sección 'notas' no encontrada, usando debug_test")
            sec = get_custom_section("debug_test")
            if not sec:
                print("   ❌ No se encontró ninguna sección con document_id")
                return False
        
        doc_id = sec.get("document_id")
        if not doc_id:
            print("   ❌ document_id no encontrado")
            return False
        
        print(f"   - Document ID: {doc_id}")
        
        # Crear workbook de prueba
        workbook = {
            "sheetData": [
                {
                    "name": "Test",
                    "celldata": [
                        {"r": 0, "c": 0, "v": {"v": "99", "m": "99", "bl": 0}}
                    ],
                    "config": {}
                }
            ]
        }
        json_str = json.dumps(workbook)
        
        # Guardar versión
        save_document_version(doc_id, json_str, comment="Test diagnóstico")
        print("   ✅ Versión de documento guardada")
        return True
    except Exception as e:
        print(f"   ❌ Error al guardar versión: {e}")
        return False


def main():
    print("🚨 DIAGNÓSTICO DE AUTO-SAVE - INICIO")
    print("=" * 50)
    
    # 1. Verificar conexión a DB
    if not test_database_connection():
        print("\n❌ ERROR: Base de datos no accesible")
        return
    
    # 2. Verificar serialización JSON
    if not test_json_serialization():
        print("\n❌ ERROR: Serialización JSON fallida")
        return
    
    # 3. Verificar actualización de sección
    if not test_section_update():
        print("\n❌ ERROR: Actualización de sección fallida")
        return
    
    # 4. Verificar guardado de versión de documento
    if not test_document_version():
        print("\n⚠️  ADVERTENCIA: Guardado de versión de documento fallido (puede ser normal si no hay document_id)")
    
    print("\n✅ DIAGNÓSTICO COMPLETADO")
    print("=" * 50)
    print("\n📋 RESULTADOS:")
    print("- Base de datos: ✅ OK")
    print("- Serialización JSON: ✅ OK")
    print("- Actualización de sección: ✅ OK")
    print("- Guardado de versión: ⚠️  Verificar manualmente")
    
    print("\n🔧 ACCIONES RECOMENDADAS:")
    print("1. Verifica que el JSON se guarda en la base de datos:")
    print("   sqlite3 school.db \"SELECT workbook_json FROM custom_sections WHERE section_key = 'debug_test';\"")
    print("2. Verifica que las versiones se guardan:")
    print("   sqlite3 school.db \"SELECT * FROM document_versions ORDER BY created_at DESC LIMIT 1;\"")
    print("3. Si el problema persiste, revisa los logs de la aplicación.")


if __name__ == "__main__":
    main()