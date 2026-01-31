# 🐳 WPA Docker Setup

Configuración completa de Docker para el sistema WPA (Workplace Process Automation).

## 📋 Requisitos Previos

- Docker Desktop instalado
- Docker Compose (incluido con Docker Desktop)
- 2GB de espacio libre en disco

## 🚀 Inicio Rápido

### Opción 1: Docker Compose (Recomendado)
```bash
# Construir e iniciar todos los servicios
docker-compose up -d --build

# Ver logs en tiempo real
docker-compose logs -f wpa

# Acceder al sistema
# URL: http://localhost:8000
# Usuario: admin
# Contraseña: admin1234
```

### Opción 2: Scripts de Utilidad

#### En Linux/Mac:
```bash
# Dar permisos de ejecución
chmod +x docker-setup.sh

# Construir e iniciar
./docker-setup.sh up

# Ver otros comandos disponibles
./docker-setup.sh help
```

#### En Windows PowerShell:
```powershell
# Construir e iniciar
.\docker-setup.ps1 up

# Ver otros comandos disponibles
.\docker-setup.ps1 help
```

### Opción 3: Comandos Docker Directos
```bash
# Construir imagen
docker build -t wpa:latest .

# Ejecutar contenedor
docker run -d \
  --name wpa-container \
  -p 8000:8000 \
  -v wpa_db:/app/db.sqlite3 \
  -v wpa_media:/app/media \
  wpa:latest
```

## 📦 Componentes Incluidos

### 🏗️ Arquitectura del Contenedor
- **Base**: Python 3.12 Alpine (liviana y segura)
- **Framework**: Django 5.x con arquitectura SOLID
- **Base de datos**: SQLite (persistente en volumen Docker)
- **Archivos media**: Volumen persistente
- **Usuario**: No-root para seguridad
- **Puerto**: 8000

### 🔧 Configuración Automática
El contenedor incluye configuración automática que:
- ✅ Aplica migraciones de base de datos
- ✅ Crea usuario admin (admin/admin1234)
- ✅ Configura tipos de campo (8 tipos)
- ✅ Carga plantillas de formularios (5 plantillas)
- ✅ Configura archivos estáticos
- ✅ Verifica el sistema

## 🎯 Credenciales por Defecto

```
Usuario: admin
Contraseña: admin1234
Monedas: 10,000
```

## 📊 Comandos Útiles

### Gestión de Contenedores
```bash
# Ver estado de servicios
docker-compose ps

# Detener servicios
docker-compose down

# Reiniciar servicios
docker-compose restart

# Ver logs
docker-compose logs -f wpa

# Acceder al shell del contenedor
docker-compose exec wpa /bin/sh
```

### Gestión de Datos
```bash
# Resetear base de datos (dentro del contenedor)
docker-compose exec wpa python manage.py reset_and_setup --force

# Backup de base de datos
docker cp wpa-app:/app/db.sqlite3 ./backup-$(date +%Y%m%d).sqlite3

# Restaurar base de datos
docker cp ./backup.sqlite3 wpa-app:/app/db.sqlite3
```

### Gestión de Volúmenes
```bash
# Ver volúmenes
docker volume ls

# Inspeccionar volumen
docker volume inspect wpa_db

# Backup completo de volúmenes
docker run --rm -v wpa_db:/source -v $(pwd):/backup alpine tar czf /backup/wpa_backup.tar.gz -C /source .
```

## 🔒 Configuración de Producción

### Variables de Entorno
```yaml
environment:
  - DEBUG=False
  - ALLOWED_HOSTS=tu-dominio.com,www.tu-dominio.com
  - SECRET_KEY=tu-clave-secreta-super-larga
  - SECURE_SSL_REDIRECT=True
  - SECURE_HSTS_SECONDS=31536000
```

### Con Base de Datos Externa (PostgreSQL)
```yaml
# Agregar al docker-compose.yml
services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: wpa
      POSTGRES_USER: wpa_user
      POSTGRES_PASSWORD: secure_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  wpa:
    environment:
      - DATABASE_URL=postgresql://wpa_user:secure_password@db:5432/wpa
```

### Con Nginx (Proxy Reverso)
```bash
# Descomentar sección nginx en docker-compose.yml
# Configurar certificados SSL
# Configurar nginx.conf para tu dominio
```

## 🛠️ Desarrollo

### Desarrollo con Volúmenes de Código
```yaml
# Para desarrollo con código en vivo
volumes:
  - .:/app
  - wpa_db:/app/db.sqlite3
  - wpa_media:/app/media
```

### Debugging
```bash
# Logs detallados
docker-compose logs -f --tail=100 wpa

# Entrar al contenedor para debug
docker-compose exec wpa /bin/sh

# Verificar configuración
docker-compose exec wpa python manage.py check --deploy
```

## 🔍 Solución de Problemas

### Problemas Comunes

#### Error de permisos
```bash
# Verificar propietario de archivos
docker-compose exec wpa ls -la /app/

# Corregir permisos si es necesario
docker-compose exec wpa chown -R wpauser:wpauser /app/
```

#### Base de datos corrupta
```bash
# Eliminar volumen y recrear
docker-compose down
docker volume rm wpa_db
docker-compose up -d
```

#### Contenedor no inicia
```bash
# Ver logs detallados
docker-compose logs wpa

# Verificar health check
docker-compose ps
```

## 📈 Monitoreo

### Health Checks
```bash
# Estado de salud del contenedor
docker inspect wpa-app | grep -A 10 Health

# Logs de health check
docker logs wpa-app 2>&1 | grep health
```

### Métricas Básicas
```bash
# Uso de recursos
docker stats wpa-app

# Espacio de volúmenes
docker system df -v
```

## 🎉 ¡Listo!

Tu sistema WPA está ahora containerizado y listo para producción. Accede a http://localhost:8000 con las credenciales admin/admin1234.

### Próximos Pasos
1. 🌐 Configura tu dominio
2. 🔒 Configura HTTPS
3. 📊 Configura monitoreo
4. 🚀 ¡Despliega en producción!