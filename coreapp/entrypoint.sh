#!/bin/bash

echo "🚀 Iniciando WPA con Docker..."

# Función para mostrar mensajes
log() {
    echo "📦 $1"
}

# Variable de entorno para indicar que estamos en Docker
export DOCKER_CONTAINER=true

# Cambiar al directorio de trabajo
cd /app

# Crear directorios necesarios con permisos correctos
log "Creando directorios necesarios..."
mkdir -p /app/db_data /app/staticfiles /app/media /app/logs
chmod -R 755 /app/db_data /app/staticfiles /app/media /app/logs

# La base de datos ahora se crea automáticamente en el volumen persistente
# No necesitamos eliminarla manualmente

# Ejecutar migraciones desde cero
log "Ejecutando migraciones iniciales..."
python manage.py migrate --noinput

if [ $? -eq 0 ]; then
    log "Migraciones completadas exitosamente"
    
    # Configurar datos iniciales
    log "Configurando datos iniciales..."
    python manage.py simple_setup --admin-user admin --admin-password admin1234 --admin-email admin@wpa.local
    
    # Configurar plantillas de formularios
    log "Configurando plantillas de formularios..."
    python manage.py setup_form_templates
else
    log "Error en migraciones"
    exit 1
fi

# Recolectar archivos estáticos
log "Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

# Verificar que todo esté funcionando
log "Verificando configuración..."
python manage.py check

log "✅ Configuración completada. Iniciando servidor..."
log "🔑 Credenciales: admin / admin1234"
log "🌐 Servidor disponible en: http://localhost:8000"

# Ejecutar el comando pasado como argumento o el servidor por defecto
if [ $# -eq 0 ]; then
    exec python manage.py runserver 0.0.0.0:8000
else
    exec "$@"
fi
