# Dockerfile para WPA - Sistema de Formularios Dinámicos con Django
FROM python:3.12-alpine

# Metadatos del contenedor
LABEL maintainer="WPA Team"
LABEL description="Sistema de formularios dinámicos con arquitectura SOLID"
LABEL version="2.0"

# Variables de entorno para Python y Django
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=coreapp.settings

# Set the working directory
WORKDIR /app

# Instalar dependencias del sistema necesarias para Django, SQLite y Pillow
RUN apk add --no-cache \
    gcc \
    musl-dev \
    sqlite \
    sqlite-dev \
    jpeg-dev \
    zlib-dev \
    freetype-dev \
    lcms2-dev \
    openjpeg-dev \
    tiff-dev \
    tk-dev \
    tcl-dev \
    harfbuzz-dev \
    fribidi-dev \
    libimagequant-dev \
    libxcb-dev \
    libpng-dev

# Crear usuario no-root para seguridad
RUN addgroup -g 1000 wpauser && \
    adduser -D -s /bin/sh -u 1000 -G wpauser wpauser

# Copy requirements first for better caching
COPY coreapp/requirements.txt ./

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY coreapp/ .

# Crear directorios necesarios
RUN mkdir -p /app/media /app/staticfiles /app/logs

# Cambiar propietario de archivos a usuario no-root
RUN chown -R wpauser:wpauser /app

# Cambiar a usuario no-root
USER wpauser

# Exponer puerto
EXPOSE 8000

# Script de entrada para configuración automática
RUN echo '#!/bin/sh' > /app/docker-entrypoint.sh && \
    echo 'set -e' >> /app/docker-entrypoint.sh && \
    echo '' >> /app/docker-entrypoint.sh && \
    echo 'echo "🚀 Iniciando WPA..."' >> /app/docker-entrypoint.sh && \
    echo '' >> /app/docker-entrypoint.sh && \
    echo '# Aplicar migraciones si es necesario' >> /app/docker-entrypoint.sh && \
    echo 'if [ ! -f "/app/db.sqlite3" ]; then' >> /app/docker-entrypoint.sh && \
    echo '    echo "📦 Configurando base de datos inicial..."' >> /app/docker-entrypoint.sh && \
    echo '    python manage.py migrate' >> /app/docker-entrypoint.sh && \
    echo '    echo "👤 Creando usuario admin..."' >> /app/docker-entrypoint.sh && \
    echo '    python manage.py reset_and_setup --force --keep-db' >> /app/docker-entrypoint.sh && \
    echo '    echo "✅ Configuración inicial completada"' >> /app/docker-entrypoint.sh && \
    echo 'else' >> /app/docker-entrypoint.sh && \
    echo '    echo "📊 Base de datos existente encontrada"' >> /app/docker-entrypoint.sh && \
    echo '    python manage.py migrate --run-syncdb' >> /app/docker-entrypoint.sh && \
    echo 'fi' >> /app/docker-entrypoint.sh && \
    echo '' >> /app/docker-entrypoint.sh && \
    echo '# Recopilar archivos estáticos' >> /app/docker-entrypoint.sh && \
    echo 'echo "📁 Recopilando archivos estáticos..."' >> /app/docker-entrypoint.sh && \
    echo 'python manage.py collectstatic --noinput --clear' >> /app/docker-entrypoint.sh && \
    echo '' >> /app/docker-entrypoint.sh && \
    echo '# Verificar sistema' >> /app/docker-entrypoint.sh && \
    echo 'echo "🔍 Verificando sistema..."' >> /app/docker-entrypoint.sh && \
    echo 'python manage.py check' >> /app/docker-entrypoint.sh && \
    echo '' >> /app/docker-entrypoint.sh && \
    echo 'echo "🌐 Iniciando servidor en puerto 8000..."' >> /app/docker-entrypoint.sh && \
    echo 'echo "📋 Credenciales: admin / admin1234"' >> /app/docker-entrypoint.sh && \
    echo 'echo "🔗 Acceso: http://localhost:8000"' >> /app/docker-entrypoint.sh && \
    echo '' >> /app/docker-entrypoint.sh && \
    echo 'exec "$@"' >> /app/docker-entrypoint.sh && \
    chmod +x /app/docker-entrypoint.sh

# Set the default command (run Django development server)
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python manage.py check || exit 1