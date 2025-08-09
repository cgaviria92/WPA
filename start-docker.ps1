# WPA - Script de arranque con Docker para PowerShell
# Autor: WPA Team
# Versión: 2.0

Write-Host ""
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "          WPA - Sistema de Formularios" -ForegroundColor White
Write-Host "           Primer arranque con Docker" -ForegroundColor White
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

# Función para mostrar mensajes con iconos
function Write-Status($message, $type = "info") {
    switch ($type) {
        "success" { Write-Host "[OK] $message" -ForegroundColor Green }
        "error" { Write-Host "[ERROR] $message" -ForegroundColor Red }
        "warning" { Write-Host "[WARNING] $message" -ForegroundColor Yellow }
        "info" { Write-Host "[INFO] $message" -ForegroundColor Blue }
        default { Write-Host "$message" }
    }
}

# Verificar si Docker está instalado
try {
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Docker está instalado: $dockerVersion" "success"
    } else {
        throw "Docker no encontrado"
    }
} catch {
    Write-Status "Docker no está instalado o no está en el PATH" "error"
    Write-Host ""
    Write-Host "Por favor instala Docker Desktop desde:"
    Write-Host "https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    Read-Host "Presiona Enter para salir"
    exit 1
}

# Verificar si Docker está corriendo
try {
    docker info 2>$null | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Docker está ejecutándose" "success"
    } else {
        throw "Docker no está corriendo"
    }
} catch {
    Write-Status "Docker no está ejecutándose" "error"
    Write-Host ""
    Write-Host "Por favor inicia Docker Desktop y vuelve a intentar"
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host ""

# Construir la imagen
Write-Host "[BUILD] Construyendo la imagen de WPA..." -ForegroundColor Yellow
try {
    docker-compose build
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Imagen construida exitosamente" "success"
    } else {
        throw "Error en construcción"
    }
} catch {
    Write-Status "Error al construir la imagen" "error"
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host ""

# Iniciar contenedores
Write-Host "[START] Iniciando los contenedores..." -ForegroundColor Yellow
try {
    docker-compose up -d
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Contenedores iniciados exitosamente" "success"
    } else {
        throw "Error al iniciar contenedores"
    }
} catch {
    Write-Status "Error al iniciar los contenedores" "error"
    Read-Host "Presiona Enter para salir"
    exit 1
}

Write-Host ""
Write-Host "[WAIT] Esperando que la aplicación esté lista..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Mostrar estado de contenedores
Write-Host ""
Write-Host "[STATUS] Estado de los contenedores:" -ForegroundColor Cyan
docker-compose ps

Write-Host ""
Write-Host "===============================================" -ForegroundColor Green
Write-Host "            WPA está listo!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""

Write-Host "Accede a la aplicación en:" -ForegroundColor Cyan
Write-Host "    http://localhost:8000" -ForegroundColor White
Write-Host ""

Write-Host "Credenciales de administrador:" -ForegroundColor Cyan
Write-Host "    Usuario: admin" -ForegroundColor White
Write-Host "    Contraseña: admin1234" -ForegroundColor White
Write-Host ""

Write-Host "Comandos útiles:" -ForegroundColor Cyan
Write-Host "    Ver logs:           docker-compose logs -f" -ForegroundColor White
Write-Host "    Parar aplicación:   docker-compose down" -ForegroundColor White
Write-Host "    Reiniciar:          docker-compose restart" -ForegroundColor White
Write-Host "    Shell del contenedor: docker-compose exec wpa sh" -ForegroundColor White
Write-Host ""

# Preguntar si abrir el navegador
$openBrowser = Read-Host "¿Quieres abrir el navegador automáticamente? (s/n)"
if ($openBrowser -eq "s" -or $openBrowser -eq "S") {
    Start-Process "http://localhost:8000"
}

Write-Host ""
Write-Host "Presiona Enter para ver los logs en tiempo real..." -ForegroundColor Yellow
Read-Host
docker-compose logs -f
