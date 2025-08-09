#!/bin/bash

# WPA - Script de arranque con Docker para Linux/Mac
# Autor: WPA Team
# Versión: 2.0

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Función para mostrar mensajes con iconos
print_status() {
    case $2 in
        "success")
            echo -e "${GREEN}✅ $1${NC}"
            ;;
        "error")
            echo -e "${RED}❌ $1${NC}"
            ;;
        "warning")
            echo -e "${YELLOW}⚠️ $1${NC}"
            ;;
        "info")
            echo -e "${BLUE}ℹ️ $1${NC}"
            ;;
        *)
            echo "$1"
            ;;
    esac
}

echo ""
echo -e "${CYAN}===============================================${NC}"
echo -e "${WHITE}          WPA - Sistema de Formularios${NC}"
echo -e "${WHITE}           Primer arranque con Docker${NC}"
echo -e "${CYAN}===============================================${NC}"
echo ""

# Verificar si Docker está instalado
if command -v docker >/dev/null 2>&1; then
    docker_version=$(docker --version)
    print_status "Docker está instalado: $docker_version" "success"
else
    print_status "Docker no está instalado" "error"
    echo ""
    echo "Por favor instala Docker desde:"
    echo -e "${YELLOW}https://docs.docker.com/get-docker/${NC}"
    read -p "Presiona Enter para salir..."
    exit 1
fi

# Verificar si Docker está corriendo
if docker info >/dev/null 2>&1; then
    print_status "Docker está ejecutándose" "success"
else
    print_status "Docker no está ejecutándose" "error"
    echo ""
    echo "Por favor inicia Docker y vuelve a intentar"
    read -p "Presiona Enter para salir..."
    exit 1
fi

# Verificar si docker-compose está disponible
if command -v docker-compose >/dev/null 2>&1; then
    compose_cmd="docker-compose"
elif docker compose version >/dev/null 2>&1; then
    compose_cmd="docker compose"
else
    print_status "docker-compose no está disponible" "error"
    exit 1
fi

echo ""

# Construir la imagen
echo -e "${YELLOW}🚀 Construyendo la imagen de WPA...${NC}"
if $compose_cmd build; then
    print_status "Imagen construida exitosamente" "success"
else
    print_status "Error al construir la imagen" "error"
    read -p "Presiona Enter para salir..."
    exit 1
fi

echo ""

# Iniciar contenedores
echo -e "${YELLOW}🐳 Iniciando los contenedores...${NC}"
if $compose_cmd up -d; then
    print_status "Contenedores iniciados exitosamente" "success"
else
    print_status "Error al iniciar los contenedores" "error"
    read -p "Presiona Enter para salir..."
    exit 1
fi

echo ""
echo -e "${YELLOW}⏳ Esperando que la aplicación esté lista...${NC}"
sleep 10

# Mostrar estado de contenedores
echo ""
echo -e "${CYAN}📊 Estado de los contenedores:${NC}"
$compose_cmd ps

echo ""
echo -e "${GREEN}===============================================${NC}"
echo -e "${GREEN}            🎉 ¡WPA está listo!${NC}"
echo -e "${GREEN}===============================================${NC}"
echo ""

echo -e "${CYAN}🔗 Accede a la aplicación en:${NC}"
echo -e "${WHITE}    http://localhost:8000${NC}"
echo ""

echo -e "${CYAN}👤 Credenciales de administrador:${NC}"
echo -e "${WHITE}    Usuario: admin${NC}"
echo -e "${WHITE}    Contraseña: admin1234${NC}"
echo ""

echo -e "${CYAN}📋 Comandos útiles:${NC}"
echo -e "${WHITE}    Ver logs:           $compose_cmd logs -f${NC}"
echo -e "${WHITE}    Parar aplicación:   $compose_cmd down${NC}"
echo -e "${WHITE}    Reiniciar:          $compose_cmd restart${NC}"
echo -e "${WHITE}    Shell del contenedor: $compose_cmd exec wpa sh${NC}"
echo ""

# Preguntar si abrir el navegador (solo en sistemas con GUI)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # Mac
    read -p "¿Quieres abrir el navegador automáticamente? (s/n): " open_browser
    if [[ $open_browser == "s" || $open_browser == "S" ]]; then
        open http://localhost:8000
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]] && command -v xdg-open >/dev/null 2>&1; then
    # Linux con GUI
    read -p "¿Quieres abrir el navegador automáticamente? (s/n): " open_browser
    if [[ $open_browser == "s" || $open_browser == "S" ]]; then
        xdg-open http://localhost:8000
    fi
fi

echo ""
echo -e "${YELLOW}Presiona Enter para ver los logs en tiempo real...${NC}"
read
$compose_cmd logs -f
