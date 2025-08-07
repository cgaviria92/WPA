# 🚀 FormBuilder Pro - Sistema de Formularios Dinámicos Multi-Tenant

¡Bienvenido a FormBuilder Pro! Una plataforma dinámica y ajustable para crear formularios sin código, con un innovador sistema de economía digital basado en monedas y **arquitectura multi-tenant** para organizaciones.

## ✨ Características Principales

- **🎯 Sin Código**: Crea formularios complejos sin programar
- **🏢 Multi-Tenant**: Cada organización tiene su propio espacio aislado
- **� Gestión de Equipos**: Invita usuarios con diferentes roles y permisos
- **�💰 Sistema de Monedas**: Cada campo tiene un costo basado en su complejidad
- **👑 Administración Avanzada**: Roles de propietario, admin, editor y visualizador
- **🔧 Completamente Dinámico**: Ajustable a cualquier necesidad
- **📊 Gestión de Respuestas**: Recolecta y analiza datos fácilmente
- **📋 Logs de Actividad**: Rastrea todas las acciones del equipo
- **🔐 Control de Acceso**: Permisos granulares por organización

## 🛠 Configuración Inicial

### 1. Instalar Dependencias
```bash
# Activar entorno virtual
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows

# Instalar Django (si no está instalado)
pip install django
```

### 2. Crear y Aplicar Migraciones
```bash
cd coreapp
python manage.py makemigrations
python manage.py migrate
```

### 3. Configurar Datos Iniciales
```bash
# Poblar tipos de campos con costos
python manage.py setup_initial_data
```

### 4. Ejecutar Servidor
```bash
python manage.py runserver
```

### 5. ¡Listo!
Visita `http://localhost:8000` y regístrate como el primer usuario para ser admin.

## 💡 Tipos de Campo y Costos

| Tipo de Campo | Costo (Monedas) | Descripción |
|---------------|-----------------|-------------|
| Número | 5 | Campos numéricos simples |
| Verdadero/Falso | 3 | Checkbox simple |
| Fecha | 8 | Selector de fecha |
| Texto Corto | 10 | Input de texto básico |
| Email | 15 | Validación de email |
| Selección | 20 | Lista desplegable |
| Texto Largo | 25 | Área de texto |
| Archivo | 50 | Subida de archivos |

## 🎮 Cómo Usar

### Registro y Configuración Inicial
1. **Regístrate** en el sistema
2. **Crea tu organización** o únete a una existente
3. **Recibe automáticamente**:
   - 1000 monedas iniciales
   - Rol de propietario de tu organización
   - Acceso completo a la gestión

### Gestión de Organizaciones
1. **Crea tu organización**: Define nombre, descripción y logo
2. **Invita miembros**: Agrega usuarios con diferentes roles:
   - **Propietario**: Control total de la organización
   - **Admin**: Gestión de usuarios y formularios (limitado)
   - **Editor**: Crear y editar formularios
   - **Visualizador**: Solo ver respuestas
3. **Gestiona permisos**: Controla quién puede hacer qué
4. **Monitorea actividad**: Ve logs detallados de todas las acciones

### Crear Formularios
1. Ve al **Dashboard** de tu organización
2. Haz clic en **"Nuevo Formulario"**
3. Completa título y descripción
4. **Agrega campos dinámicamente**:
   - Selecciona tipo de campo
   - Define etiqueta y ayuda
   - Configura si es obligatorio
   - ¡Paga con tus monedas!

### Gestionar Economía
- **Cada campo cuesta monedas** según su complejidad
- **Reembolso del 50%** al eliminar campos
- **Monitorea transacciones** en tiempo real por organización
- **Los administradores pueden otorgar monedas** a miembros del equipo

## 🏗 Estructura del Proyecto

```
coreapp/
├── mainapp/
│   ├── models.py          # Modelos de datos
│   ├── views.py           # Lógica de vistas
│   ├── forms.py           # Formularios Django
│   ├── admin.py           # Configuración admin
│   ├── urls.py            # URLs de la app
│   ├── templates/         # Plantillas HTML
│   ├── templatetags/      # Filtros personalizados
│   └── management/        # Comandos personalizados
├── coreapp/
│   ├── settings.py        # Configuración Django
│   └── urls.py            # URLs principales
└── manage.py
```

## 🎨 Funcionalidades Avanzadas

### Sistema Multi-Tenant
- Organizaciones completamente aisladas
- Datos y usuarios separados por organización
- Configuraciones independientes por empresa
- Escalabilidad para múltiples clientes

### Gestión de Equipos y Roles
- **Propietario**: Control total de organización y configuraciones
- **Administrador**: Gestión de usuarios y formularios (sin configuraciones)
- **Editor**: Crear y modificar formularios, ver respuestas
- **Visualizador**: Solo acceso de lectura a formularios y respuestas
- Invitaciones por email y gestión masiva de usuarios

### Sistema de Monedas por Organización
- Costos dinámicos basados en complejidad del campo
- Multiplicadores de almacenamiento
- Historial completo de transacciones por organización
- Reembolsos por eliminación de campos
- Gestión independiente por organización

### Logs y Auditoría
- Registro completo de actividades por organización
- Filtros avanzados por usuario, acción y fecha
- Exportación de logs para auditorías
- Limpieza automática de logs antiguos
- Trazabilidad completa de cambios

### Formularios Dinámicos
- Campos configurables en tiempo real
- Validaciones automáticas
- Ordenamiento mediante drag & drop
- Vista previa en tiempo real
- Formularios públicos y privados por organización

## 🐛 Solución de Problemas

### "No hay tipos de campo disponibles"
```bash
python manage.py setup_initial_data
```

### Errores de migración
```bash
python manage.py makemigrations mainapp
python manage.py migrate
```

### Resetear base de datos
```bash
# CUIDADO: Esto borra todos los datos
rm db.sqlite3
python manage.py migrate
python manage.py setup_initial_data
```

## 🚀 Próximas Características

- [ ] Dashboard analítico avanzado por organización
- [ ] Sistema de plantillas de formularios compartidas
- [ ] Exportación de datos (CSV, Excel) con filtros avanzados
- [ ] Notificaciones por email y webhooks
- [ ] API REST para integraciones con sistemas externos
- [ ] Temas personalizables por organización
- [ ] Análisis y estadísticas avanzadas con gráficos
- [ ] Integración con servicios de pago para monedas
- [ ] Sistema de backup y restauración por organización
- [ ] Modo offline para formularios

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la licencia MIT.

---

**¡Creado con ❤️ para hacer que la creación de formularios sea fácil y divertida!**

¿Necesitas ayuda? Abre un issue en GitHub o contacta al equipo de desarrollo.
