"""
Servicios y clases base orientadas a objetos para WPA
Sistema de Formularios Dinámicos
"""

from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.utils.text import slugify
from django.http import JsonResponse
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
import logging

from .models import (
    CustomUser, Organization, OrganizationMembership, FieldType,
    DynamicForm, DynamicFormField, FormSubmission, CoinTransaction,
    ActivityLog, FormTemplate, InventoryItem, InventoryTransaction
)

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Excepción base para errores de servicios"""
    pass


class InsufficientCoinsError(ServiceError):
    """Error cuando el usuario no tiene suficientes monedas"""
    def __init__(self, required: int, available: int):
        self.required = required
        self.available = available
        super().__init__(f"Necesitas {required} monedas, pero solo tienes {available}")


class PermissionError(ServiceError):
    """Error de permisos"""
    pass


class BaseService:
    """Clase base para todos los servicios"""
    
    def __init__(self, user: CustomUser, request=None):
        self.user = user
        self.request = request
    
    def log_activity(self, action: str, description: str, 
                    organization: Organization = None, 
                    form: DynamicForm = None):
        """Registrar actividad del usuario"""
        try:
            ActivityLog.objects.create(
                user=self.user,
                organization=organization,
                action=action,
                description=description,
                related_form=form,
                ip_address=self._get_client_ip(),
                user_agent=self._get_user_agent()
            )
        except Exception as e:
            logger.error(f"Error al registrar actividad: {e}")
    
    def _get_client_ip(self) -> str:
        """Obtener IP del cliente"""
        if not self.request:
            return "unknown"
        
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return self.request.META.get('REMOTE_ADDR', 'unknown')
    
    def _get_user_agent(self) -> str:
        """Obtener User Agent"""
        if not self.request:
            return ""
        return self.request.META.get('HTTP_USER_AGENT', '')


class CoinService(BaseService):
    """Servicio para manejo de monedas"""
    
    def check_balance(self, required_amount: int) -> bool:
        """Verificar si el usuario tiene suficientes monedas"""
        return self.user.monedas >= required_amount
    
    def spend_coins(self, amount: int, description: str, 
                   organization: Organization = None,
                   form: DynamicForm = None) -> CoinTransaction:
        """Gastar monedas del usuario"""
        if not self.check_balance(amount):
            raise InsufficientCoinsError(amount, self.user.monedas)
        
        with transaction.atomic():
            # Actualizar saldo del usuario
            self.user.monedas -= amount
            self.user.save()
            
            # Crear transacción
            coin_transaction = CoinTransaction.objects.create(
                user=self.user,
                organization=organization,
                transaction_type='spend',
                amount=amount,
                description=description,
                related_form=form
            )
            
            # Registrar actividad
            self.log_activity(
                'coin_spend',
                f'Monedas gastadas: {amount} - {description}',
                organization=organization,
                form=form
            )
            
            return coin_transaction
    
    def refund_coins(self, amount: int, description: str,
                    organization: Organization = None,
                    form: DynamicForm = None) -> CoinTransaction:
        """Reembolsar monedas al usuario"""
        with transaction.atomic():
            # Actualizar saldo del usuario
            self.user.monedas += amount
            self.user.save()
            
            # Crear transacción
            coin_transaction = CoinTransaction.objects.create(
                user=self.user,
                organization=organization,
                transaction_type='refund',
                amount=amount,
                description=description,
                related_form=form
            )
            
            # Registrar actividad
            self.log_activity(
                'coin_refund',
                f'Monedas reembolsadas: {amount} - {description}',
                organization=organization,
                form=form
            )
            
            return coin_transaction


class OrganizationService(BaseService):
    """Servicio para manejo de organizaciones"""
    
    def get_user_organization(self, org_slug: str) -> Tuple[Organization, OrganizationMembership]:
        """Obtener organización y membresía del usuario"""
        organization = get_object_or_404(Organization, slug=org_slug, is_active=True)
        
        try:
            membership = OrganizationMembership.objects.get(
                user=self.user,
                organization=organization,
                is_active=True
            )
            return organization, membership
        except OrganizationMembership.DoesNotExist:
            raise PermissionError("No tienes acceso a esta organización")
    
    def check_permission(self, organization: Organization, permission: str) -> OrganizationMembership:
        """Verificar permisos específicos en una organización"""
        try:
            membership = OrganizationMembership.objects.get(
                user=self.user,
                organization=organization,
                is_active=True
            )
        except OrganizationMembership.DoesNotExist:
            raise PermissionError("No tienes acceso a esta organización")
        
        permission_methods = {
            'edit_forms': membership.can_edit_forms,
            'view_submissions': membership.can_view_submissions,
            'manage_users': membership.can_manage_users,
            'manage_organization': membership.can_manage_organization,
        }
        
        if permission not in permission_methods:
            raise ValueError(f"Permiso desconocido: {permission}")
        
        if not permission_methods[permission]():
            raise PermissionError(f"No tienes permisos para: {permission}")
        
        return membership


class FormService(BaseService):
    """Servicio para manejo de formularios dinámicos"""
    
    def __init__(self, user: CustomUser, request=None):
        super().__init__(user, request)
        self.coin_service = CoinService(user, request)
        self.org_service = OrganizationService(user, request)
    
    def calculate_form_cost(self, field_types: List[FieldType]) -> int:
        """Calcular costo total de un formulario"""
        return sum(field_type.cost for field_type in field_types)
    
    def calculate_template_cost(self, template: FormTemplate) -> int:
        """Calcular costo de una plantilla"""
        total_cost = 0
        template_data = template.template_data
        
        for field_data in template_data.get('fields', []):
            try:
                field_type = FieldType.objects.get(name=field_data['field_type'])
                total_cost += field_type.cost
            except FieldType.DoesNotExist:
                logger.warning(f"Tipo de campo no encontrado: {field_data['field_type']}")
                continue
        
        return total_cost
    
    def create_form_from_template(self, organization: Organization, template: FormTemplate,
                                 title: str = None, description: str = None,
                                 is_public: bool = False) -> DynamicForm:
        """Crear formulario desde plantilla"""
        
        # Verificar permisos
        self.org_service.check_permission(organization, 'edit_forms')
        
        # Calcular costo
        template_cost = self.calculate_template_cost(template)
        
        # Verificar monedas
        if not self.coin_service.check_balance(template_cost):
            raise InsufficientCoinsError(template_cost, self.user.monedas)
        
        with transaction.atomic():
            # Crear formulario
            form = DynamicForm.objects.create(
                organization=organization,
                creator=self.user,
                title=title or template.name,
                description=description or template.description,
                is_public=is_public,
                total_cost=template_cost
            )
            
            # Crear campos
            template_data = template.template_data
            for i, field_data in enumerate(template_data.get('fields', [])):
                try:
                    field_type = FieldType.objects.get(name=field_data['field_type'])
                    
                    DynamicFormField.objects.create(
                        form=form,
                        field_type=field_type,
                        label=field_data['label'],
                        help_text=field_data.get('help_text', ''),
                        is_required=field_data.get('is_required', False),
                        choices=field_data.get('choices', ''),
                        order=i
                    )
                    
                except FieldType.DoesNotExist:
                    logger.warning(f"Tipo de campo no encontrado: {field_data['field_type']}")
                    continue
            
            # Gastar monedas
            self.coin_service.spend_coins(
                template_cost,
                f'Formulario creado desde plantilla: {template.name}',
                organization=organization,
                form=form
            )
            
            # Crear lógica de negocio si existe
            if template.business_logic:
                from .models import BusinessLogicProcessor
                BusinessLogicProcessor.objects.create(
                    form=form,
                    logic_type=template.category,
                    python_code=template.business_logic,
                    config_data={'template_id': template.id}
                )
            
            # Incrementar contador de uso
            template.usage_count += 1
            template.save()
            
            # Registrar actividad
            self.log_activity(
                'create_form_from_template',
                f'Formulario "{form.title}" creado desde plantilla "{template.name}"',
                organization=organization,
                form=form
            )
            
            return form


class ProgressTracker:
    """Clase para manejar el progreso de operaciones largas"""
    
    def __init__(self, total_steps: int, session_key: str = None):
        self.total_steps = total_steps
        self.current_step = 0
        self.session_key = session_key or 'progress'
        self.messages = []
    
    def update(self, step: int = None, message: str = ""):
        """Actualizar progreso"""
        if step is not None:
            self.current_step = step
        else:
            self.current_step += 1
        
        if message:
            self.messages.append(message)
        
        return self.get_progress_data()
    
    def get_progress_data(self) -> Dict:
        """Obtener datos de progreso"""
        percentage = min(100, (self.current_step / self.total_steps) * 100)
        
        return {
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'percentage': round(percentage, 1),
            'messages': self.messages,
            'completed': self.current_step >= self.total_steps
        }
    
    def to_json_response(self) -> JsonResponse:
        """Convertir a respuesta JSON"""
        return JsonResponse(self.get_progress_data())


class AsyncTaskManager:
    """Gestor para tareas asíncronas (simulado)"""
    
    @staticmethod
    def start_form_creation_task(user_id: int, org_slug: str, template_id: int,
                                form_data: Dict) -> str:
        """Iniciar tarea de creación de formulario"""
        # En una implementación real, esto usaría Celery o similar
        # Por ahora, simulamos con un ID de tarea
        import uuid
        task_id = str(uuid.uuid4())
        
        # Simular el guardado del estado de la tarea
        # En producción, esto se guardaría en Redis o similar
        
        return task_id
    
    @staticmethod
    def get_task_progress(task_id: str) -> Dict:
        """Obtener progreso de una tarea"""
        # Simulación de progreso
        # En producción, esto consultaría el estado real de la tarea
        
        return {
            'task_id': task_id,
            'status': 'PROGRESS',
            'current': 75,
            'total': 100,
            'message': 'Creando campos del formulario...'
        }
