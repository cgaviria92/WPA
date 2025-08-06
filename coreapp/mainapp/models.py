from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
import json

class CustomUser(AbstractUser):
    monedas = models.IntegerField(default=1000)
    is_admin_user = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Si es el primer usuario, se convierte en admin y obtiene monedas extra
        if not self.pk and not CustomUser.objects.exists():
            self.is_admin_user = True
            self.is_staff = True
            self.is_superuser = True
            self.monedas = 1000  # Monedas iniciales para el admin
        super().save(*args, **kwargs)
    
    def can_afford(self, cost):
        return self.monedas >= cost
    
    def spend_coins(self, amount):
        if self.can_afford(amount):
            self.monedas -= amount
            self.save()
            return True
        return False


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
        return f"{self.display_name} (${self.cost} monedas)"


class DynamicForm(models.Model):
    """Formulario dinámico creado por usuarios"""
    creator = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='created_forms')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    total_cost = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def calculate_total_cost(self):
        return sum(field.field_type.cost for field in self.fields.all())
    
    def __str__(self):
        return self.title


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
    
    def __str__(self):
        return f"Envío de {self.form.title} - {self.submitted_at}"


class CoinTransaction(models.Model):
    """Registro de transacciones de monedas"""
    TRANSACTION_TYPES = [
        ('spend', 'Gasto'),
        ('earn', 'Ganancia'),
        ('admin_grant', 'Otorgado por Admin'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.IntegerField()
    description = models.CharField(max_length=500)
    related_form = models.ForeignKey(DynamicForm, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - {self.amount} monedas"
