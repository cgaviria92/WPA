# 🚀 FormBuilder Pro - Sistema de Formularios Dinámicos

¡Bienvenido a FormBuilder Pro! Una plataforma dinámica y ajustable para crear formularios sin código, con un innovador sistema de economía digital basado en monedas.

## ✨ Características Principales

- **🎯 Sin Código**: Crea formularios complejos sin programar
- **💰 Sistema de Monedas**: Cada campo tiene un costo basado en su complejidad
- **👑 Primer Usuario Admin**: El primer registrado obtiene privilegios especiales
- **🔧 Completamente Dinámico**: Ajustable a cualquier necesidad
- **📊 Gestión de Respuestas**: Recolecta y analiza datos fácilmente

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

### Como Primer Usuario (Admin)
1. **Regístrate** como el primer usuario del sistema
2. **Recibe automáticamente**:
   - Privilegios de administrador
   - 1000 monedas iniciales
   - Acceso completo al sistema

### Crear Formularios
1. Ve al **Dashboard**
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
- **Monitorea transacciones** en tiempo real
- **Los administradores pueden otorgar monedas** a otros usuarios

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

### Sistema de Monedas
- Costos dinámicos basados en complejidad del campo
- Multiplicadores de almacenamiento
- Historial completo de transacciones
- Reembolsos por eliminación de campos

### Gestión de Usuarios
- Primer usuario automáticamente admin
- Sistema de roles y permisos
- Tracking de actividad por usuario

### Formularios Dinámicos
- Campos configurables en tiempo real
- Validaciones automáticas
- Ordenamiento mediante drag & drop
- Vista previa en tiempo real

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

- [ ] Sistema de plantillas de formularios
- [ ] Exportación de datos (CSV, Excel)
- [ ] Notificaciones por email
- [ ] API REST para integraciones
- [ ] Temas personalizables
- [ ] Análisis y estadísticas avanzadas

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
