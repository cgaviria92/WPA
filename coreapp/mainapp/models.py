from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
import json

class CustomUser(AbstractUser):
    monedas = models.IntegerField(default=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    is_admin_user = models.BooleanField(default=False, verbose_name="Es usuario administrador")
    
    def __str__(self):
        return self.username


class Organization(models.Model):
    """Organización/Empresa - Sistema Multi-Tenant"""
    name = models.CharField(max_length=200, verbose_name="Nombre de la Organización")
    description = models.TextField(blank=True, verbose_name="Descripción")
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='owned_organizations', 
                             verbose_name="Propietario")
    slug = models.SlugField(unique=True, verbose_name="Slug único")
    logo = models.ImageField(upload_to='organizations/', blank=True, null=True, verbose_name="Logo")
    is_active = models.BooleanField(default=True, verbose_name="Activa")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Configuraciones
    max_users = models.IntegerField(default=10, verbose_name="Máximo de usuarios")
    max_forms = models.IntegerField(default=50, verbose_name="Máximo de formularios")
    
    class Meta:
        verbose_name = "Organización"
        verbose_name_plural = "Organizaciones"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def can_add_user(self):
        return self.memberships.filter(is_active=True).count() < self.max_users
    
    def can_add_form(self):
        return self.forms.filter(is_active=True).count() < self.max_forms


class OrganizationMembership(models.Model):
    """Membresía de usuario en organización con roles"""
    ROLE_CHOICES = [
        ('owner', 'Propietario'),
        ('admin', 'Administrador'),
        ('editor', 'Editor'),
        ('viewer', 'Visualizador'),
        ('form_filler', 'Llenador de Formularios'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='memberships')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    is_active = models.BooleanField(default=True)
    invited_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, 
                                   related_name='invitations_sent')
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'organization']
        verbose_name = "Membresía"
        verbose_name_plural = "Membresías"
    
    def __str__(self):
        return f"{self.user.username} - {self.organization.name} ({self.get_role_display()})"
    
    def can_edit_forms(self):
        return self.role in ['owner', 'admin', 'editor']
    
    def can_view_submissions(self):
        return self.role in ['owner', 'admin', 'editor', 'viewer']
    
    def can_manage_users(self):
        return self.role in ['owner', 'admin']


class FieldType(models.Model):
    """Tipos de campos disponibles con sus costos"""
    FIELD_TYPES = [
        ('text', 'Texto Corto'),
        ('textarea', 'Texto Largo'),
        ('number', 'Número'),
        ('email', 'Email'),
        ('date', 'Fecha'),
        ('file', 'Archivo'),
        ('boolean', 'Verdadero/Falso'),
        ('choice', 'Selección'),
    ]
    
    name = models.CharField(max_length=50, choices=FIELD_TYPES, unique=True)
    display_name = models.CharField(max_length=100)
    cost = models.IntegerField(help_text="Costo en monedas para usar este tipo de campo")
    storage_multiplier = models.FloatField(default=1.0, help_text="Multiplicador de costo por almacenamiento")
    
    def __str__(self):
        return f"{self.display_name} ({self.cost} monedas)"


class DynamicForm(models.Model):
    """Formulario dinámico creado por usuarios dentro de una organización"""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='forms')
    creator = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_forms')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False, help_text="¿Puede ser llenado por usuarios no registrados?")
    total_cost = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def calculate_total_cost(self):
        return sum(field.field_type.cost for field in self.fields.all())
    
    def __str__(self):
        return f"{self.organization.name} - {self.title}"


class DynamicFormField(models.Model):
    """Campo dinámico de un formulario"""
    form = models.ForeignKey(DynamicForm, on_delete=models.CASCADE, related_name='fields')
    field_type = models.ForeignKey(FieldType, on_delete=models.CASCADE)
    label = models.CharField(max_length=200)
    help_text = models.CharField(max_length=500, blank=True)
    is_required = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    # Para campos de selección
    choices = models.TextField(blank=True, help_text="Opciones separadas por líneas para campos de selección")
    
    # Configuraciones adicionales
    max_length = models.IntegerField(null=True, blank=True, help_text="Para campos de texto")
    min_value = models.FloatField(null=True, blank=True, help_text="Para campos numéricos")
    max_value = models.FloatField(null=True, blank=True, help_text="Para campos numéricos")
    
    # Configuraciones para campos de archivo
    max_file_size_mb = models.FloatField(
        null=True, blank=True, default=5.0,
        help_text="Tamaño máximo del archivo en MB (por defecto 5 MB)"
    )
    allowed_file_types = models.CharField(
        max_length=500, blank=True,
        default="image/*,application/pdf,.doc,.docx,.txt",
        help_text="Tipos de archivo permitidos separados por comas (ej: image/*,application/pdf,.txt)"
    )
    file_cost_per_mb = models.FloatField(
        null=True, blank=True, default=1.0,
        help_text="Costo en monedas por MB de archivo subido"
    )
    
    class Meta:
        ordering = ['order']
    
    def get_choices_list(self):
        if self.choices:
            return [choice.strip() for choice in self.choices.split('\n') if choice.strip()]
        return []
    
    def get_allowed_file_types_list(self):
        """Devuelve lista de tipos de archivo permitidos"""
        if self.allowed_file_types:
            return [ftype.strip() for ftype in self.allowed_file_types.split(',') if ftype.strip()]
        return ['image/*', 'application/pdf', '.txt']
    
    def calculate_file_cost(self, file_size_bytes):
        """Calcula el costo de subir un archivo basado en su tamaño"""
        if not self.file_cost_per_mb or file_size_bytes <= 0:
            return 0
        
        size_mb = file_size_bytes / (1024 * 1024)  # Convertir bytes a MB
        return max(1, int(size_mb * self.file_cost_per_mb))  # Mínimo 1 moneda
    
    def validate_file_size(self, file_size_bytes):
        """Valida que el archivo no exceda el tamaño máximo"""
        if not self.max_file_size_mb:
            return True
        
        max_size_bytes = self.max_file_size_mb * 1024 * 1024
        return file_size_bytes <= max_size_bytes
    
    def get_max_file_size_bytes(self):
        """Devuelve el tamaño máximo en bytes"""
        return int((self.max_file_size_mb or 5.0) * 1024 * 1024)
    
    def __str__(self):
        return f"{self.form.title} - {self.label}"


class FormSubmission(models.Model):
    """Envío de datos a un formulario dinámico"""
    form = models.ForeignKey(DynamicForm, on_delete=models.CASCADE, related_name='submissions')
    submitted_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    data = models.JSONField(help_text="Datos del formulario en formato JSON")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"Envío de {self.form.title} - {self.submitted_at}"


class UploadedFile(models.Model):
    """Archivo subido a través de un formulario"""
    submission = models.ForeignKey(FormSubmission, on_delete=models.CASCADE, related_name='files')
    field = models.ForeignKey(DynamicFormField, on_delete=models.CASCADE)
    file = models.FileField(upload_to='uploads/%Y/%m/%d/')
    original_name = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField(help_text="Tamaño en bytes")
    mime_type = models.CharField(max_length=100)
    cost_charged = models.PositiveIntegerField(default=0, help_text="Monedas cobradas por este archivo")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.original_name} ({self.get_file_size_display()})"
    
    def get_file_size_display(self):
        """Devuelve el tamaño del archivo en formato legible"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"


class CoinTransaction(models.Model):
    """Registro de transacciones de monedas"""
    TRANSACTION_TYPES = [
        ('spend', 'Gasto'),
        ('earn', 'Ganancia'),
        ('admin_grant', 'Otorgado por Admin'),
        ('refund', 'Reembolso'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='transactions')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True, 
                                   related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.IntegerField()
    description = models.CharField(max_length=500)
    related_form = models.ForeignKey(DynamicForm, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.amount} monedas"


class ActivityLog(models.Model):
    """Log de actividades del sistema"""
    ACTION_TYPES = [
        ('create_organization', 'Crear Organización'),
        ('create_form', 'Crear Formulario'),
        ('edit_form', 'Editar Formulario'),
        ('delete_form', 'Eliminar Formulario'),
        ('add_field', 'Agregar Campo'),
        ('remove_field', 'Eliminar Campo'),
        ('invite_user', 'Invitar Usuario'),
        ('change_role', 'Cambiar Rol'),
        ('submit_form', 'Enviar Formulario'),
        ('login', 'Iniciar Sesión'),
        ('logout', 'Cerrar Sesión'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activity_logs')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, null=True, blank=True,
                                   related_name='activity_logs')
    action = models.CharField(max_length=30, choices=ACTION_TYPES)
    description = models.TextField()
    related_form = models.ForeignKey(DynamicForm, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Log de Actividad"
        verbose_name_plural = "Logs de Actividad"
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_display()} - {self.created_at}"


class FormTemplate(models.Model):
    """Plantillas predefinidas de formularios para diferentes casos de uso"""
    CATEGORY_CHOICES = [
        ('inventory', 'Inventario'),
        ('sales', 'Ventas'),
        ('hr', 'Recursos Humanos'),
        ('customer', 'Atención al Cliente'),
        ('finance', 'Finanzas'),
        ('general', 'General'),
    ]
    
    name = models.CharField(max_length=200, verbose_name="Nombre de la Plantilla")
    description = models.TextField(verbose_name="Descripción")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name="Categoría")
    icon = models.CharField(max_length=50, default="fas fa-file-alt", verbose_name="Icono Font Awesome")
    
    # Configuración de la plantilla
    template_data = models.JSONField(verbose_name="Datos de la plantilla")
    business_logic = models.TextField(blank=True, verbose_name="Lógica de negocio (Python)")
    
    # Metadatos
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    usage_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['category', 'name']
        verbose_name = "Plantilla de Formulario"
        verbose_name_plural = "Plantillas de Formularios"
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.name}"


class InventoryItem(models.Model):
    """Artículos de inventario para lógica de negocio"""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='inventory_items')
    name = models.CharField(max_length=200, verbose_name="Nombre del artículo")
    description = models.TextField(blank=True, verbose_name="Descripción")
    sku = models.CharField(max_length=100, verbose_name="SKU/Código")
    
    # Stock y precios
    current_stock = models.IntegerField(default=0, verbose_name="Stock actual")
    min_stock = models.IntegerField(default=5, verbose_name="Stock mínimo")
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio de compra")
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio de venta")
    
    # Metadatos
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['organization', 'sku']
        ordering = ['name']
        verbose_name = "Artículo de Inventario"
        verbose_name_plural = "Artículos de Inventario"
    
    def __str__(self):
        return f"{self.name} ({self.sku}) - Stock: {self.current_stock}"
    
    @property
    def profit_margin(self):
        """Calcular margen de ganancia"""
        if self.purchase_price > 0:
            return ((self.sale_price - self.purchase_price) / self.purchase_price) * 100
        return 0
    
    @property
    def needs_restock(self):
        """Verificar si necesita reabastecimiento"""
        return self.current_stock <= self.min_stock


class InventoryTransaction(models.Model):
    """Transacciones de inventario (compras, ventas, ajustes)"""
    TRANSACTION_TYPES = [
        ('purchase', 'Compra'),
        ('sale', 'Venta'),
        ('adjustment', 'Ajuste'),
        ('return', 'Devolución'),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='inventory_transactions')
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    
    # Detalles de la transacción
    quantity = models.IntegerField(verbose_name="Cantidad")
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio unitario")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total")
    
    # Referencias
    reference_number = models.CharField(max_length=100, blank=True, verbose_name="Número de referencia")
    notes = models.TextField(blank=True, verbose_name="Notas")
    
    # Relacionado con formularios
    related_form_submission = models.ForeignKey(FormSubmission, on_delete=models.SET_NULL, 
                                              null=True, blank=True, verbose_name="Envío de formulario relacionado")
    
    # Metadatos
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Transacción de Inventario"
        verbose_name_plural = "Transacciones de Inventario"
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.item.name} x{self.quantity}"
    
    def save(self, *args, **kwargs):
        """Actualizar stock automáticamente"""
        # Calcular total
        self.total_amount = self.quantity * self.unit_price
        
        # Guardar transacción
        super().save(*args, **kwargs)
        
        # Actualizar stock del artículo
        if self.transaction_type in ['purchase', 'return']:
            self.item.current_stock += self.quantity
        elif self.transaction_type in ['sale']:
            self.item.current_stock -= self.quantity
        elif self.transaction_type == 'adjustment':
            # Para ajustes, la cantidad puede ser positiva o negativa
            self.item.current_stock = self.quantity
        
        self.item.save()


class BusinessLogicProcessor(models.Model):
    """Procesador de lógica de negocio para formularios"""
    form = models.OneToOneField(DynamicForm, on_delete=models.CASCADE, related_name='business_logic')
    logic_type = models.CharField(max_length=50, choices=[
        ('inventory', 'Gestión de Inventario'),
        ('sales', 'Procesamiento de Ventas'),
        ('calculations', 'Cálculos Automáticos'),
        ('notifications', 'Notificaciones'),
        ('custom', 'Lógica Personalizada'),
    ])
    
    # Configuración de la lógica
    config_data = models.JSONField(default=dict, verbose_name="Configuración")
    python_code = models.TextField(blank=True, verbose_name="Código Python personalizado")
    
    # Estado
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Lógica de Negocio"
        verbose_name_plural = "Lógicas de Negocio"
    
    def __str__(self):
        return f"{self.form.title} - {self.get_logic_type_display()}"
