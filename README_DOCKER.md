# WPA - Arranque con Docker 🐳

Este archivo contiene las instrucciones para ejecutar WPA usando Docker de forma fácil y rápida.

## 🚀 Arranque Rápido

### Windows

#### Opción 1: Script Batch (Recomendado)
```cmd
.\start-docker.bat
```

#### Opción 2: PowerShell
```powershell
.\start-docker.ps1
```

#### Opción 3: Manual
```cmd
docker-compose build
docker-compose up -d
```

### Linux/Mac

#### Opción 1: Script automatizado (Recomendado)
```bash
chmod +x start-docker.sh
./start-docker.sh
```

#### Opción 2: Manual
```bash
docker-compose build
docker-compose up -d
```

## 📋 Requisitos Previos

1. **Docker Desktop** instalado y ejecutándose
   - Windows/Mac: [Docker Desktop](https://www.docker.com/products/docker-desktop)
   - Linux: [Docker Engine](https://docs.docker.com/engine/install/)

2. **Docker Compose** (incluido en Docker Desktop)

## 🔗 Acceso a la Aplicación

Una vez iniciado, accede a:
- **URL**: http://localhost:8000
- **Usuario**: admin
- **Contraseña**: admin1234

## 📊 Comandos Útiles

```bash
# Ver logs en tiempo real
docker-compose logs -f

# Parar la aplicación
docker-compose down

# Reiniciar la aplicación
docker-compose restart

# Ver estado de contenedores
docker-compose ps

# Acceder al shell del contenedor
docker-compose exec wpa sh

# Reconstruir desde cero
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🔧 Configuración Avanzada

### Variables de Entorno

Puedes personalizar la configuración creando un archivo `.env`:

```env
# .env
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,tu-dominio.com
SECRET_KEY=tu-clave-secreta-aqui
```

### Volúmenes Persistentes

Los datos se almacenan en volúmenes Docker:
- `wpa_db`: Base de datos SQLite
- `wpa_media`: Archivos subidos por usuarios
- `wpa_logs`: Logs de la aplicación
- `wpa_static`: Archivos estáticos

### Desarrollo con Hot-Reload

Para desarrollo con recarga automática, descomenta la línea en `docker-compose.yml`:

```yaml
volumes:
  # Para desarrollo: montar código fuente
  - ./coreapp:/app
```

## 🔍 Solución de Problemas

### Puerto 8000 ya está en uso
```bash
# Encontrar proceso usando el puerto
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# Cambiar puerto en docker-compose.yml
ports:
  - "8001:8000"  # Usa puerto 8001 en lugar de 8000
```

### Error de permisos
```bash
# Linux/Mac: Asegurar permisos correctos
sudo chown -R $USER:$USER .
chmod +x start-docker.sh
```

### Contenedor no inicia
```bash
# Ver logs detallados
docker-compose logs wpa

# Verificar estado
docker-compose ps

# Reiniciar desde cero
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

### Base de datos corrupta
```bash
# Eliminar volumen de base de datos
docker-compose down
docker volume rm wpa_wpa_db
docker-compose up -d
```

## 🏗️ Arquitectura del Contenedor

- **Base**: Python 3.12 Alpine (ligero y seguro)
- **Puerto**: 8000
- **Usuario**: wpauser (no-root para seguridad)
- **Servicios**: Django + SQLite
- **Auto-configuración**: Migraciones y datos iniciales automáticos

## 📝 Notas Importantes

1. **Primer arranque**: Puede tardar unos minutos en descargar e instalar dependencias
2. **Datos persistentes**: Los datos se mantienen entre reinicios gracias a los volúmenes Docker
3. **Seguridad**: El contenedor ejecuta con usuario no-root
4. **Logs**: Los logs se almacenan tanto en el contenedor como en volúmenes persistentes

## 🆘 Soporte

Si encuentras problemas:

1. Revisa los logs: `docker-compose logs -f`
2. Verifica que Docker esté ejecutándose
3. Asegúrate de que el puerto 8000 esté libre
4. Intenta reiniciar desde cero con los comandos de solución de problemas

---

**¡WPA está listo para usar! 🎉**
