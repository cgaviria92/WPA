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

# Instalar dependencias del sistema necesarias para Django, SQLite y Pillow + curl para healthcheck
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
    libpng-dev \
    curl \
    bash

# Copiar requirements y instalar dependencias
COPY coreapp/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar archivos de proyecto
COPY coreapp/ /app/

# Configurar permisos y entrypoint
RUN chmod +x /app/entrypoint.sh

# Crear directorios necesarios
RUN mkdir -p /app/media /app/staticfiles /app/logs /app/data

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Usar nuestro entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]