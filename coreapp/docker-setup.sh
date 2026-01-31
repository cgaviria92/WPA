#!/bin/bash
# Script para construir y ejecutar WPA con Docker

echo "🐳 WPA Docker Setup"
echo "==================="

# Función para mostrar ayuda
show_help() {
    echo "Uso: ./docker-setup.sh [COMANDO]"
    echo ""
    echo "Comandos disponibles:"
    echo "  build    - Construir la imagen Docker"
    echo "  run      - Ejecutar el contenedor"
    echo "  up       - Construir y ejecutar con docker-compose"
    echo "  down     - Detener y eliminar contenedores"
    echo "  logs     - Ver logs del contenedor"
    echo "  shell    - Acceder al shell del contenedor"
    echo "  reset    - Resetear base de datos"
    echo "  help     - Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  ./docker-setup.sh build"
    echo "  ./docker-setup.sh up"
    echo "  ./docker-setup.sh logs"
}

# Función para construir la imagen
build_image() {
    echo "🔨 Construyendo imagen Docker..."
    docker build -t wpa:latest .
    echo "✅ Imagen construida exitosamente"
}

# Función para ejecutar el contenedor
run_container() {
    echo "🚀 Ejecutando contenedor..."
    docker run -d \
        --name wpa-container \
        -p 8000:8000 \
        -v wpa_db:/app/db.sqlite3 \
        -v wpa_media:/app/media \
        wpa:latest
    echo "✅ Contenedor ejecutándose en http://localhost:8000"
    echo "👤 Usuario: admin"
    echo "🔑 Contraseña: admin1234"
}

# Función para docker-compose up
compose_up() {
    echo "🚀 Iniciando servicios con Docker Compose..."
    docker-compose up -d --build
    echo "✅ Servicios iniciados exitosamente"
    echo "🌐 Acceso: http://localhost:8000"
    echo "👤 Usuario: admin"
    echo "🔑 Contraseña: admin1234"
}

# Función para docker-compose down
compose_down() {
    echo "🛑 Deteniendo servicios..."
    docker-compose down
    echo "✅ Servicios detenidos"
}

# Función para ver logs
show_logs() {
    echo "📋 Mostrando logs..."
    if docker ps | grep -q wpa-app; then
        docker-compose logs -f wpa
    else
        docker logs -f wpa-container 2>/dev/null || echo "❌ Contenedor no encontrado"
    fi
}

# Función para acceder al shell
access_shell() {
    echo "💻 Accediendo al shell del contenedor..."
    if docker ps | grep -q wpa-app; then
        docker-compose exec wpa /bin/sh
    else
        docker exec -it wpa-container /bin/sh 2>/dev/null || echo "❌ Contenedor no encontrado"
    fi
}

# Función para resetear base de datos
reset_database() {
    echo "🗃️ Reseteando base de datos..."
    read -p "⚠️ ¿Estás seguro? Esto eliminará todos los datos (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if docker ps | grep -q wpa-app; then
            docker-compose exec wpa python manage.py reset_and_setup --force
        else
            docker exec -it wpa-container python manage.py reset_and_setup --force 2>/dev/null || echo "❌ Contenedor no encontrado"
        fi
        echo "✅ Base de datos reseteada"
    else
        echo "❌ Operación cancelada"
    fi
}

# Procesar argumentos
case "$1" in
    build)
        build_image
        ;;
    run)
        build_image
        run_container
        ;;
    up)
        compose_up
        ;;
    down)
        compose_down
        ;;
    logs)
        show_logs
        ;;
    shell)
        access_shell
        ;;
    reset)
        reset_database
        ;;
    help|--help|-h)
        show_help
        ;;
    "")
        echo "❌ Error: Se requiere un comando"
        echo ""
        show_help
        exit 1
        ;;
    *)
        echo "❌ Error: Comando desconocido '$1'"
        echo ""
        show_help
        exit 1
        ;;
esac