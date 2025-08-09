# Script PowerShell para gestionar WPA con Docker
param(
    [string]$Command
)

function Show-Help {
    Write-Host "🐳 WPA Docker Setup" -ForegroundColor Cyan
    Write-Host "===================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Uso: .\docker-setup.ps1 [COMANDO]" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Comandos disponibles:" -ForegroundColor Green
    Write-Host "  build    - Construir la imagen Docker" -ForegroundColor White
    Write-Host "  run      - Ejecutar el contenedor" -ForegroundColor White
    Write-Host "  up       - Construir y ejecutar con docker-compose" -ForegroundColor White
    Write-Host "  down     - Detener y eliminar contenedores" -ForegroundColor White
    Write-Host "  logs     - Ver logs del contenedor" -ForegroundColor White
    Write-Host "  shell    - Acceder al shell del contenedor" -ForegroundColor White
    Write-Host "  reset    - Resetear base de datos" -ForegroundColor White
    Write-Host "  help     - Mostrar esta ayuda" -ForegroundColor White
    Write-Host ""
    Write-Host "Ejemplos:" -ForegroundColor Yellow
    Write-Host "  .\docker-setup.ps1 build" -ForegroundColor Gray
    Write-Host "  .\docker-setup.ps1 up" -ForegroundColor Gray
    Write-Host "  .\docker-setup.ps1 logs" -ForegroundColor Gray
}

function Build-Image {
    Write-Host "🔨 Construyendo imagen Docker..." -ForegroundColor Yellow
    docker build -t wpa:latest .
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Imagen construida exitosamente" -ForegroundColor Green
    } else {
        Write-Host "❌ Error al construir la imagen" -ForegroundColor Red
        exit 1
    }
}

function Run-Container {
    Write-Host "🚀 Ejecutando contenedor..." -ForegroundColor Yellow
    docker run -d --name wpa-container -p 8000:8000 -v wpa_db:/app/db.sqlite3 -v wpa_media:/app/media wpa:latest
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Contenedor ejecutándose en http://localhost:8000" -ForegroundColor Green
        Write-Host "👤 Usuario: admin" -ForegroundColor Cyan
        Write-Host "🔑 Contraseña: admin1234" -ForegroundColor Cyan
    } else {
        Write-Host "❌ Error al ejecutar el contenedor" -ForegroundColor Red
    }
}

function Compose-Up {
    Write-Host "🚀 Iniciando servicios con Docker Compose..." -ForegroundColor Yellow
    docker-compose up -d --build
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Servicios iniciados exitosamente" -ForegroundColor Green
        Write-Host "🌐 Acceso: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "👤 Usuario: admin" -ForegroundColor Cyan
        Write-Host "🔑 Contraseña: admin1234" -ForegroundColor Cyan
    } else {
        Write-Host "❌ Error al iniciar servicios" -ForegroundColor Red
    }
}

function Compose-Down {
    Write-Host "🛑 Deteniendo servicios..." -ForegroundColor Yellow
    docker-compose down
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Servicios detenidos" -ForegroundColor Green
    } else {
        Write-Host "❌ Error al detener servicios" -ForegroundColor Red
    }
}

function Show-Logs {
    Write-Host "📋 Mostrando logs..." -ForegroundColor Yellow
    $containerRunning = docker ps --filter "name=wpa-app" --format "{{.Names}}"
    if ($containerRunning) {
        docker-compose logs -f wpa
    } else {
        $containerExists = docker ps -a --filter "name=wpa-container" --format "{{.Names}}"
        if ($containerExists) {
            docker logs -f wpa-container
        } else {
            Write-Host "❌ Contenedor no encontrado" -ForegroundColor Red
        }
    }
}

function Access-Shell {
    Write-Host "💻 Accediendo al shell del contenedor..." -ForegroundColor Yellow
    $containerRunning = docker ps --filter "name=wpa-app" --format "{{.Names}}"
    if ($containerRunning) {
        docker-compose exec wpa /bin/sh
    } else {
        $containerExists = docker ps --filter "name=wpa-container" --format "{{.Names}}"
        if ($containerExists) {
            docker exec -it wpa-container /bin/sh
        } else {
            Write-Host "❌ Contenedor no encontrado" -ForegroundColor Red
        }
    }
}

function Reset-Database {
    Write-Host "🗃️ Reseteando base de datos..." -ForegroundColor Yellow
    $confirmation = Read-Host "⚠️ ¿Estás seguro? Esto eliminará todos los datos (y/n)"
    if ($confirmation -eq 'y' -or $confirmation -eq 'Y' -or $confirmation -eq 'yes') {
        $containerRunning = docker ps --filter "name=wpa-app" --format "{{.Names}}"
        if ($containerRunning) {
            docker-compose exec wpa python manage.py reset_and_setup --force
        } else {
            $containerExists = docker ps --filter "name=wpa-container" --format "{{.Names}}"
            if ($containerExists) {
                docker exec -it wpa-container python manage.py reset_and_setup --force
            } else {
                Write-Host "❌ Contenedor no encontrado" -ForegroundColor Red
                return
            }
        }
        Write-Host "✅ Base de datos reseteada" -ForegroundColor Green
    } else {
        Write-Host "❌ Operación cancelada" -ForegroundColor Red
    }
}

# Procesar comandos
switch ($Command.ToLower()) {
    "build" {
        Build-Image
    }
    "run" {
        Build-Image
        Run-Container
    }
    "up" {
        Compose-Up
    }
    "down" {
        Compose-Down
    }
    "logs" {
        Show-Logs
    }
    "shell" {
        Access-Shell
    }
    "reset" {
        Reset-Database
    }
    "help" {
        Show-Help
    }
    "" {
        Write-Host "❌ Error: Se requiere un comando" -ForegroundColor Red
        Write-Host ""
        Show-Help
        exit 1
    }
    default {
        Write-Host "❌ Error: Comando desconocido '$Command'" -ForegroundColor Red
        Write-Host ""
        Show-Help
        exit 1
    }
}
