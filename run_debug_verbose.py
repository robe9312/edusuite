#!/usr/bin/env python3
"""
Script para ejecutar EduSuite en modo debug con logs detallados.
"""

import sys
import traceback
from PySide6.QtWidgets import QApplication

print("🚀 Iniciando EduSuite en modo debug detallado...")

# 1. Inicializar base de datos
try:
    from db.database import init_db
    init_db()
    print("✅ Base de datos inicializada")
except Exception as e:
    print(f"❌ Error al inicializar DB: {e}")
    traceback.print_exc()
    sys.exit(1)

# 2. Crear QApplication
try:
    app = QApplication(sys.argv)
    print("✅ QApplication creada")
    print(f"🔍 QApplication: {app}")
except Exception as e:
    print(f"❌ Error al crear QApplication: {e}")
    traceback.print_exc()
    sys.exit(1)

# 3. Aplicar estilos
try:
    from ui_style import apply_global_style
    apply_global_style(app)
    print("✅ Estilos aplicados")
except Exception as e:
    print(f"❌ Error al aplicar estilos: {e}")
    traceback.print_exc()
    sys.exit(1)

# 4. Crear y mostrar MainWindow directamente (sin login)
try:
    from views.main_window import MainWindow
    print("🔍 Creando MainWindow...")
    window = MainWindow()
    print(f"✅ MainWindow creada: {window}")
    print("🔍 Mostrando MainWindow...")
    window.show()
    print("✅ MainWindow mostrada")
    print(f"🔍 MainWindow geometry: {window.geometry()}")
except Exception as e:
    print(f"❌ Error al mostrar ventana principal: {e}")
    traceback.print_exc()
    sys.exit(1)

# 5. Ejecutar event loop
print("🎉 Aplicación iniciada correctamente")
print("🔄 Ejecutando event loop...")
print(f"🔍 QApplication.topLevelWidgets(): {QApplication.topLevelWidgets()}")

try:
    print("🚀 Iniciando event loop...")
    ret = app.exec()
    print(f"🎬 Event loop finalizado con código: {ret}")
    sys.exit(ret)
except Exception as e:
    print(f"❌ Error en event loop: {e}")
    traceback.print_exc()
    sys.exit(1)