#!/bin/bash
set -e

echo "🚀 Iniciando WPA - Sistema de Formularios Dinámicos"
echo "================================================="

# Función para logging con timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Variable de entorno para indicar que estamos en Docker
export DOCKER_CONTAINER=true

# Cambiar al directorio de trabajo
cd /app

# Crear directorios necesarios con permisos correctos
log "📁 Creando directorios necesarios..."
mkdir -p /app/db_data /app/staticfiles /app/media /app/logs
chmod -R 755 /app/db_data /app/staticfiles /app/media /app/logs

# Esperar a que la base de datos esté disponible
log "⏳ Verificando conexión a la base de datos..."
python << END
import sys
import time
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coreapp.settings')
django.setup()

from django.db import connections
from django.db.utils import OperationalError

db_conn = connections['default']
for i in range(30):
    try:
        db_conn.ensure_connection()
        print("✅ Base de datos disponible!")
        break
    except OperationalError:
        print(f"🔄 Base de datos no disponible, reintentando... ({i+1}/30)")
        time.sleep(1)
else:
    print("❌ Error: No se pudo conectar a la base de datos")
    sys.exit(1)
END

# Crear migraciones automáticamente para todas las apps
log "🔄 Creando migraciones automáticas..."
python manage.py makemigrations --noinput

# Ejecutar migraciones
log "📊 Aplicando migraciones..."
python manage.py migrate --noinput

if [ $? -eq 0 ]; then
    log "✅ Migraciones completadas exitosamente"
    
    # Configurar datos iniciales
    log "🗃️  Configurando datos iniciales..."
    python manage.py simple_setup --admin-user admin --admin-password admin1234 --admin-email admin@wpa.local
    
    # Configurar plantillas de formularios
    log "📋 Configurando plantillas de formularios..."
    python manage.py setup_form_templates
else
    log "❌ Error en migraciones"
    exit 1
fi

# Recolectar archivos estáticos
log "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

# Verificar que todo esté funcionando
log "🔍 Verificando configuración..."
python manage.py check

log "✅ Inicialización completada exitosamente!"
log "🌐 Iniciando servidor..."

# Obtener puerto de variable de entorno o usar 8000 por defecto
PORT=${PORT:-8000}
log "📍 URL: http://localhost:${PORT}"
log "👤 Usuario: admin | 🔑 Contraseña: admin1234"
echo "================================================="

# Determinar si estamos en modo producción (DEBUG=False)
# Convertir a minúsculas y comparar
DEBUG_LOWER=$(echo "$DEBUG" | tr '[:upper:]' '[:lower:]')
if [ "$DEBUG_LOWER" = "false" ] || [ "$DEBUG_LOWER" = "0" ] || [ -z "$DEBUG_LOWER" ]; then
    log "🚀 Modo producción: Iniciando Gunicorn..."
    # Usar Gunicorn para producción
    exec gunicorn coreapp.wsgi:application --bind 0.0.0.0:${PORT} --workers 3 --access-logfile -
else
    log "🔧 Modo desarrollo: Iniciando servidor Django..."
    # Usar runserver para desarrollo
    exec python manage.py runserver 0.0.0.0:${PORT}
fi
