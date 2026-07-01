#!/usr/bin/env python3
"""
Script para ejecutar EduSuite en modo debug sin login.
"""

import sys
from PySide6.QtWidgets import QApplication

print("🚀 Iniciando EduSuite en modo debug...")

# 1. Inicializar base de datos
try:
    from db.database import init_db
    init_db()
    print("✅ Base de datos inicializada")
except Exception as e:
    print(f"❌ Error al inicializar DB: {e}")
    sys.exit(1)

# 2. Crear QApplication
try:
    app = QApplication(sys.argv)
    print("✅ QApplication creada")
except Exception as e:
    print(f"❌ Error al crear QApplication: {e}")
    sys.exit(1)

# 3. Aplicar estilos
try:
    from ui_style import apply_global_style
    apply_global_style(app)
    print("✅ Estilos aplicados")
except Exception as e:
    print(f"❌ Error al aplicar estilos: {e}")
    sys.exit(1)

# 4. Crear y mostrar MainWindow directamente (sin login)
try:
    from views.main_window import MainWindow
    window = MainWindow()
    window.show()
    print("✅ MainWindow creada y mostrada")
except Exception as e:
    print(f"❌ Error al mostrar ventana principal: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 5. Ejecutar event loop
print("🎉 Aplicación iniciada correctamente")
print("🔄 Ejecutando event loop...")
sys.exit(app.exec())