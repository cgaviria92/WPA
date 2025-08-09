# Script para probar la construcción de Docker de WPA
Write-Host "🐳 WPA - Prueba de Docker Build" -ForegroundColor Cyan
Write-Host "===============================" -ForegroundColor Cyan

# Cambiar al directorio del proyecto
Set-Location "c:\Users\ingca\OneDrive\Desktop\personal\wpa"

Write-Host "📁 Directorio actual: $(Get-Location)" -ForegroundColor Yellow

# Verificar que los archivos necesarios existen
$requiredFiles = @(
    "Dockerfile",
    "docker-compose.yml", 
    ".dockerignore",
    "coreapp\requirements.txt",
    "coreapp\manage.py"
)

Write-Host "`n🔍 Verificando archivos necesarios..." -ForegroundColor Yellow
$allFilesExist = $true

foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "✅ $file" -ForegroundColor Green
    } else {
        Write-Host "❌ $file - NO ENCONTRADO" -ForegroundColor Red
        $allFilesExist = $false
    }
}

if (-not $allFilesExist) {
    Write-Host "`n❌ Faltan archivos necesarios. Cancelandooperación." -ForegroundColor Red
    exit 1
}

Write-Host "`n🔨 Construyendo imagen Docker..." -ForegroundColor Yellow
Write-Host "Esto puede tomar unos minutos la primera vez..." -ForegroundColor Gray

# Construir la imagen
docker build -t wpa:latest .

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ ¡Imagen construida exitosamente!" -ForegroundColor Green
    
    Write-Host "`n🚀 Para ejecutar el contenedor:" -ForegroundColor Cyan
    Write-Host "docker-compose up -d" -ForegroundColor White
    Write-Host "`n🌐 Acceder a: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "👤 Usuario: admin" -ForegroundColor Cyan
    Write-Host "🔑 Contraseña: admin1234" -ForegroundColor Cyan
    
    Write-Host "`n📋 Otros comandos útiles:" -ForegroundColor Yellow
    Write-Host "docker-compose logs -f wpa  # Ver logs" -ForegroundColor White
    Write-Host "docker-compose down         # Detener" -ForegroundColor White
    Write-Host "docker-compose exec wpa /bin/sh  # Shell" -ForegroundColor White
} else {
    Write-Host "`n❌ Error al construir la imagen" -ForegroundColor Red
    Write-Host "Revisa los mensajes de error arriba." -ForegroundColor Gray
    exit 1
}
