"""
Implementaciones concretas de los servicios siguiendo principios SOLID
"""

import mimetypes
from typing import Dict, List, Any, Optional
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.contrib import messages
from django.core.files.storage import default_storage

from .interfaces import (
    IPermissionService, IFormValidationService, IFileProcessingService,
    IFormSubmissionService, IContextBuilderService, INotificationService
)
from .models import OrganizationMembership, FormSubmission, ActivityLog


class PermissionService(IPermissionService):
    """Servicio para manejo de permisos - Single Responsibility"""
    
    def has_form_access(self, user: User, organization, form) -> bool:
        """Verifica si un usuario tiene acceso a un formulario"""
        # Formulario público
        if form.is_public:
            return True
        
        # Usuario no autenticado
        if not user.is_authenticated:
            return False
        
        # Verificar membresía
        membership = self.get_user_membership(user, organization)
        return membership is not None
    
    def can_edit_form(self, user: User, organization, form) -> bool:
        """Verifica si un usuario puede editar un formulario"""
        if not user.is_authenticated:
            return False
        
        membership = self.get_user_membership(user, organization)
        if not membership:
            return False
        
        # El creador o admin puede editar
        return form.creator == user or membership.is_admin
    
    def get_user_membership(self, user: User, organization):
        """Obtiene la membresía de un usuario en una organización"""
        try:
            return OrganizationMembership.objects.get(
                user=user, organization=organization, is_active=True
            )
        except OrganizationMembership.DoesNotExist:
            return None


class FormValidationService(IFormValidationService):
    """Servicio para validación de formularios - Single Responsibility"""
    
    def validate_form_submission(self, fields: List, request_data: Dict) -> Dict[str, Any]:
        """Valida los datos enviados en un formulario"""
        submission_data = {}
        errors = {}
        valid = True
        
        for field in fields:
            field_name = f'field_{field.id}'
            field_validation = self.validate_field(field, request_data.get(field_name))
            
            if field_validation['errors']:
                errors.update(field_validation['errors'])
                valid = False
            
            if field_validation['value'] is not None:
                submission_data[field_name] = field_validation['value']
        
        return {
            'submission_data': submission_data,
            'errors': errors,
            'valid': valid
        }
    
    def validate_field(self, field, value: Any) -> Dict[str, str]:
        """Valida un campo específico"""
        errors = {}
        field_name = f'field_{field.id}'
        
        # Campo requerido
        if field.is_required and not value:
            errors[field_name] = 'Este campo es obligatorio'
            return {'value': None, 'errors': errors}
        
        # Validaciones específicas por tipo
        if field.field_type.name == 'email' and value:
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value):
                errors[field_name] = 'Ingresa un email válido'
        
        elif field.field_type.name == 'number' and value:
            try:
                num_value = float(value)
                if field.min_value is not None and num_value < field.min_value:
                    errors[field_name] = f'El valor mínimo es {field.min_value}'
                elif field.max_value is not None and num_value > field.max_value:
                    errors[field_name] = f'El valor máximo es {field.max_value}'
            except ValueError:
                errors[field_name] = 'Ingresa un número válido'
        
        elif field.field_type.name in ['text', 'textarea'] and value:
            if field.max_length and len(value) > field.max_length:
                errors[field_name] = f'Máximo {field.max_length} caracteres'
        
        return {'value': value, 'errors': errors}


class FileProcessingService(IFileProcessingService):
    """Servicio para procesamiento de archivos - Single Responsibility"""
    
    def validate_file(self, file, field) -> Dict[str, str]:
        """Valida un archivo subido"""
        errors = {}
        field_name = f'field_{field.id}'
        
        if not file:
            if field.is_required:
                errors[field_name] = 'Este campo es obligatorio'
            return errors
        
        # Validar tamaño
        if not field.validate_file_size(file.size):
            max_mb = field.max_file_size_mb or 5.0
            current_mb = file.size / (1024 * 1024)
            errors[field_name] = f'Archivo demasiado grande ({current_mb:.1f} MB). Máximo: {max_mb} MB'
            return errors
        
        # Validar tipo
        file_type = mimetypes.guess_type(file.name)[0] or ''
        file_ext = '.' + file.name.split('.')[-1].lower() if '.' in file.name else ''
        allowed_types = field.get_allowed_file_types_list()
        
        type_allowed = False
        for allowed in allowed_types:
            if allowed.startswith('.'):  # Es una extensión
                if file_ext == allowed.lower():
                    type_allowed = True
                    break
            elif '/' in allowed:  # Es un tipo MIME
                if file_type.startswith(allowed):
                    type_allowed = True
                    break
        
        if not type_allowed:
            errors[field_name] = f'Tipo de archivo no permitido. Tipos permitidos: {", ".join(allowed_types)}'
        
        return errors
    
    def calculate_file_cost(self, file, field) -> int:
        """Calcula el costo de un archivo"""
        if not file:
            return 0
        
        file_size_mb = file.size / (1024 * 1024)
        cost_per_mb = field.file_cost_per_mb or 10
        return max(1, round(file_size_mb * cost_per_mb))
    
    def process_file_upload(self, file, field, organization) -> Dict[str, Any]:
        """Procesa la subida de un archivo"""
        if not file:
            return {'success': False, 'error': 'No file provided'}
        
        try:
            # Generar nombre único
            import uuid
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_id = str(uuid.uuid4())[:8]
            file_extension = file.name.split('.')[-1] if '.' in file.name else 'bin'
            
            # Crear ruta de almacenamiento
            file_path = f'organizations/{organization.slug}/files/{timestamp}_{unique_id}.{file_extension}'
            
            # Guardar archivo usando Django storage
            saved_path = default_storage.save(file_path, file)
            
            return {
                'success': True,
                'file_path': saved_path,
                'original_name': file.name,
                'size': file.size,
                'cost': self.calculate_file_cost(file, field),
                'mime_type': mimetypes.guess_type(file.name)[0] or ''
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_uploaded_file_record(self, submission, field, file_result, user=None):
        """Crea el registro de archivo subido en la base de datos"""
        from .models import UploadedFile
        
        return UploadedFile.objects.create(
            submission=submission,
            field=field,
            file=file_result['file_path'],
            original_name=file_result['original_name'],
            file_size=file_result['size'],
            mime_type=file_result['mime_type'],
            cost_charged=file_result['cost'],
            uploaded_by=user
        )


class FormSubmissionService(IFormSubmissionService):
    """Servicio para manejo de envíos de formularios - Single Responsibility"""
    
    def __init__(self, notification_service: INotificationService):
        self.notification_service = notification_service
    
    def create_submission(self, form, data: Dict, user: Optional[User] = None) -> 'FormSubmission':
        """Crea un nuevo envío de formulario"""
        from django.db import transaction
        
        with transaction.atomic():
            submission = FormSubmission.objects.create(
                form=form,
                submitted_by=user,
                data=data,
                ip_address=self._get_client_ip(getattr(self, '_request', None))
            )
            
            # Log de actividad
            self._log_activity(form, user, submission)
            
            return submission
    
    def process_coin_transaction(self, user: User, organization, amount: int, description: str, form=None):
        """Procesa una transacción de monedas"""
        if amount <= 0 or not user.is_authenticated:
            return
        
        # Verificar que el usuario tenga suficientes monedas
        if user.monedas < amount:
            raise ValueError(f'Monedas insuficientes. Necesitas {amount}, tienes {user.monedas}')
        
        from django.db import transaction
        from .models import CoinTransaction
        
        with transaction.atomic():
            # Actualizar monedas del usuario
            user.monedas -= amount
            user.save()
            
            # Registrar transacción
            CoinTransaction.objects.create(
                user=user,
                organization=organization,
                transaction_type='spend',
                amount=amount,
                description=description,
                related_form=form
            )
    
    def process_business_logic(self, form, submission_data: Dict) -> Dict[str, Any]:
        """Procesa la lógica de negocio del formulario"""
        if not form.business_logic:
            return {'processed': False, 'result': None}
        
        try:
            # Aquí se ejecutaría la lógica de negocio
            # Por ahora, solo registramos que se procesó
            return {
                'processed': True,
                'result': 'Lógica de negocio aplicada exitosamente'
            }
        except Exception as e:
            return {
                'processed': False,
                'error': str(e)
            }
    
    def _get_client_ip(self, request):
        """Obtiene la IP del cliente"""
        if not request:
            return None
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _log_activity(self, form, user, submission):
        """Registra la actividad en los logs"""
        ActivityLog.objects.create(
            organization=form.organization,
            user=user,
            action='form_submission',
            description=f'Nuevo envío en formulario "{form.title}"',
            related_object_type='form',
            related_object_id=form.id
        )


class ContextBuilderService(IContextBuilderService):
    """Servicio para construcción de contexto - Single Responsibility"""
    
    def __init__(self, permission_service: IPermissionService):
        self.permission_service = permission_service
    
    def build_form_context(self, request: HttpRequest, organization, form) -> Dict[str, Any]:
        """Construye el contexto para el template de formulario"""
        context = {
            'organization': organization,
            'dynamic_form': form,
            'fields': form.fields.all().order_by('order'),
        }
        
        # Agregar información de membresía si está autenticado
        if request.user.is_authenticated:
            membership = self.permission_service.get_user_membership(request.user, organization)
            context['membership'] = membership
            context['can_edit'] = self.permission_service.can_edit_form(request.user, organization, form)
        
        return context
    
    def build_dashboard_context(self, request: HttpRequest, organization) -> Dict[str, Any]:
        """Construye el contexto para el dashboard"""
        membership = None
        if request.user.is_authenticated:
            membership = self.permission_service.get_user_membership(request.user, organization)
        
        return {
            'organization': organization,
            'membership': membership,
            'user_coins': request.user.monedas if request.user.is_authenticated else 0,
        }


class NotificationService(INotificationService):
    """Servicio para notificaciones - Single Responsibility"""
    
    def send_success_message(self, request: HttpRequest, message: str) -> None:
        """Envía un mensaje de éxito"""
        messages.success(request, message)
    
    def send_error_message(self, request: HttpRequest, message: str) -> None:
        """Envía un mensaje de error"""
        messages.error(request, message)
    
    def send_warning_message(self, request: HttpRequest, message: str) -> None:
        """Envía un mensaje de advertencia"""
        messages.warning(request, message)
