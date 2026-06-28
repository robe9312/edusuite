#!/bin/bash
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

# Cargar variables de entorno desde archivo .env si existe
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

export QT_AUTO_SCREEN_SCALE_FACTOR=1
export QT_ENABLE_HIGHDPI_SCALING=1
exec python3 main.py
