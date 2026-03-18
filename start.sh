#!/bin/bash
# ── start.sh — Inicia la app en producción con gunicorn ─────────────────────
# Uso: bash start.sh [puerto]

PORT=${1:-5000}
WORKERS=2
TIMEOUT=120

# Crear carpetas necesarias
mkdir -p uploads static

echo "▶  Iniciando Solar·Arch en puerto $PORT con $WORKERS workers..."
gunicorn wsgi:application \
    --bind "0.0.0.0:$PORT" \
    --workers "$WORKERS" \
    --timeout "$TIMEOUT" \
    --access-logfile - \
    --error-logfile - \
    --log-level info
