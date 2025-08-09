@echo off
echo.
echo ===============================================
echo          WPA - Sistema de Formularios
echo           Primer arranque con Docker
echo ===============================================
echo.

REM Verificar si Docker está instalado
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Docker no está instalado o no está en el PATH
    echo.
    echo Por favor instala Docker Desktop desde:
    echo https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Verificar si Docker está corriendo
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Docker no está ejecutándose
    echo.
    echo Por favor inicia Docker Desktop y vuelve a intentar
    pause
    exit /b 1
)

echo ✅ Docker está disponible
echo.

echo 🚀 Construyendo la imagen de WPA...
docker-compose build

if errorlevel 1 (
    echo ❌ Error al construir la imagen
    pause
    exit /b 1
)

echo.
echo 🐳 Iniciando los contenedores...
docker-compose up -d

if errorlevel 1 (
    echo ❌ Error al iniciar los contenedores
    pause
    exit /b 1
)

echo.
echo ⏳ Esperando que la aplicación esté lista...
timeout /t 10 /nobreak >nul

REM Verificar que el contenedor esté corriendo
docker-compose ps

echo.
echo ===============================================
echo            🎉 ¡WPA está listo!
echo ===============================================
echo.
echo 🔗 Accede a la aplicación en:
echo    http://localhost:8000
echo.
echo 👤 Credenciales de administrador:
echo    Usuario: admin
echo    Contraseña: admin1234
echo.
echo 📋 Comandos útiles:
echo    Ver logs:           docker-compose logs -f
echo    Parar aplicación:   docker-compose down
echo    Reiniciar:          docker-compose restart
echo    Shell del contenedor: docker-compose exec wpa sh
echo.

REM Preguntar si abrir el navegador
set /p open_browser="¿Quieres abrir el navegador automáticamente? (s/n): "
if /i "%open_browser%"=="s" (
    start http://localhost:8000
)

echo.
echo Presiona cualquier tecla para ver los logs en tiempo real...
pause >nul
docker-compose logs -f
