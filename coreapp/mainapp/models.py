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
    
    class Meta:
        ordering = ['order']
    
    def get_choices_list(self):
        if self.choices:
            return [choice.strip() for choice in self.choices.split('\n') if choice.strip()]
        return []
    
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
