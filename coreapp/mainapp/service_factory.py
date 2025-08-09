"""
Factory para crear servicios siguiendo principios SOLID
Aplica Dependency Inversion y facilita el testing
"""

from typing import Dict, Type
from .interfaces import (
    IPermissionService, IFormValidationService, IFileProcessingService,
    IFormSubmissionService, IContextBuilderService, INotificationService
)
from .solid_services import (
    PermissionService, FormValidationService, FileProcessingService,
    FormSubmissionService, ContextBuilderService, NotificationService
)


class ServiceFactory:
    """Factory para crear servicios - aplicando Dependency Inversion Principle"""
    
    _services: Dict[str, object] = {}
    _service_classes: Dict[str, Type] = {
        'permission': PermissionService,
        'validation': FormValidationService,
        'file_processing': FileProcessingService,
        'submission': FormSubmissionService,
        'context_builder': ContextBuilderService,
        'notification': NotificationService,
    }
    
    @classmethod
    def get_permission_service(cls) -> IPermissionService:
        """Obtiene el servicio de permisos"""
        if 'permission' not in cls._services:
            cls._services['permission'] = cls._service_classes['permission']()
        return cls._services['permission']
    
    @classmethod
    def get_validation_service(cls) -> IFormValidationService:
        """Obtiene el servicio de validación"""
        if 'validation' not in cls._services:
            cls._services['validation'] = cls._service_classes['validation']()
        return cls._services['validation']
    
    @classmethod
    def get_file_processing_service(cls) -> IFileProcessingService:
        """Obtiene el servicio de procesamiento de archivos"""
        if 'file_processing' not in cls._services:
            cls._services['file_processing'] = cls._service_classes['file_processing']()
        return cls._services['file_processing']
    
    @classmethod
    def get_submission_service(cls) -> IFormSubmissionService:
        """Obtiene el servicio de envíos"""
        if 'submission' not in cls._services:
            notification_service = cls.get_notification_service()
            cls._services['submission'] = cls._service_classes['submission'](notification_service)
        return cls._services['submission']
    
    @classmethod
    def get_context_builder_service(cls) -> IContextBuilderService:
        """Obtiene el servicio de construcción de contexto"""
        if 'context_builder' not in cls._services:
            permission_service = cls.get_permission_service()
            cls._services['context_builder'] = cls._service_classes['context_builder'](permission_service)
        return cls._services['context_builder']
    
    @classmethod
    def get_notification_service(cls) -> INotificationService:
        """Obtiene el servicio de notificaciones"""
        if 'notification' not in cls._services:
            cls._services['notification'] = cls._service_classes['notification']()
        return cls._services['notification']
    
    @classmethod
    def register_service(cls, service_name: str, service_class: Type) -> None:
        """Registra un nuevo servicio - Open/Closed Principle"""
        cls._service_classes[service_name] = service_class
        # Limpiar la instancia cacheada si existe
        if service_name in cls._services:
            del cls._services[service_name]
    
    @classmethod
    def clear_cache(cls) -> None:
        """Limpia el cache de servicios - útil para testing"""
        cls._services.clear()


class FormProcessor:
    """
    Procesador principal de formularios siguiendo SOLID
    Orquesta los diferentes servicios sin violar SRP
    """
    
    def __init__(self):
        self.permission_service = ServiceFactory.get_permission_service()
        self.validation_service = ServiceFactory.get_validation_service()
        self.file_processing_service = ServiceFactory.get_file_processing_service()
        self.submission_service = ServiceFactory.get_submission_service()
        self.context_builder_service = ServiceFactory.get_context_builder_service()
        self.notification_service = ServiceFactory.get_notification_service()
        self._current_request = None
    
    def check_form_access(self, user, organization, form) -> bool:
        """Verifica acceso al formulario"""
        return self.permission_service.has_form_access(user, organization, form)
    
    def process_form_submission(self, request, organization, form) -> Dict:
        """Procesa el envío de un formulario completo"""
        from django.db import transaction
        
        # Establecer el request actual para el servicio
        self.submission_service._request = request
        
        # 1. Obtener campos
        fields = form.fields.all().order_by('order')
        
        # 2. Validar datos básicos
        validation_result = self.validation_service.validate_form_submission(
            fields, {**request.POST.dict(), **request.FILES.dict()}
        )
        
        if not validation_result['valid']:
            return {
                'success': False,
                'errors': validation_result['errors']
            }
        
        # 3. Procesar archivos
        file_results = self._process_files(request, fields, organization)
        if not file_results['success']:
            return file_results
        
        # 4. Verificar monedas para archivos
        total_cost = file_results['total_cost']
        if total_cost > 0 and request.user.is_authenticated:
            if request.user.monedas < total_cost:
                return {
                    'success': False,
                    'error': f'Monedas insuficientes. Necesitas {total_cost}, tienes {request.user.monedas}'
                }
        
        # 5. Crear envío en transacción atómica
        try:
            with transaction.atomic():
                # Crear envío con datos básicos
                submission_data = validation_result['submission_data'].copy()
                submission = self.submission_service.create_submission(
                    form, submission_data, request.user if request.user.is_authenticated else None
                )
                
                # Procesar archivos y actualizar submission_data
                uploaded_files = []
                for file_info in file_results['file_info']:
                    uploaded_file_obj = self.file_processing_service.create_uploaded_file_record(
                        submission, file_info['field'], file_info['file_result'], 
                        request.user if request.user.is_authenticated else None
                    )
                    
                    # Actualizar submission_data con la URL del archivo
                    field_name = f'field_{file_info["field"].id}'
                    submission_data[field_name] = uploaded_file_obj.file.url
                    uploaded_files.append(uploaded_file_obj.original_name)
                
                # Actualizar submission con las URLs de archivos
                submission.data = submission_data
                submission.save()
                
                # Procesar transacción de monedas
                if total_cost > 0 and request.user.is_authenticated:
                    self.submission_service.process_coin_transaction(
                        request.user, organization, total_cost,
                        f'Subida de archivos en formulario: {form.title}',
                        form
                    )
                
                # Procesar lógica de negocio
                business_result = self.submission_service.process_business_logic(form, submission_data)
                
                return {
                    'success': True,
                    'submission': submission,
                    'business_result': business_result,
                    'file_cost': total_cost,
                    'uploaded_files': uploaded_files
                }
                
        except ValueError as e:
            return {'success': False, 'error': str(e)}
        except Exception as e:
            return {'success': False, 'error': f'Error al procesar envío: {str(e)}'}
    
    def _process_files(self, request, fields, organization) -> Dict:
        """Procesa archivos subidos"""
        file_info = []
        total_cost = 0
        
        for field in fields:
            if field.field_type.name == 'file':
                field_name = f'field_{field.id}'
                uploaded_file = request.FILES.get(field_name)
                
                if uploaded_file:
                    # Validar archivo
                    validation_errors = self.file_processing_service.validate_file(uploaded_file, field)
                    if validation_errors:
                        return {'success': False, 'errors': validation_errors}
                    
                    # Procesar archivo
                    file_result = self.file_processing_service.process_file_upload(
                        uploaded_file, field, organization
                    )
                    
                    if not file_result['success']:
                        return {'success': False, 'error': file_result['error']}
                    
                    file_info.append({
                        'field': field,
                        'file_result': file_result
                    })
                    total_cost += file_result['cost']
        
        return {
            'success': True,
            'file_info': file_info,
            'total_cost': total_cost
        }
    
    def build_context(self, request, organization, form) -> Dict:
        """Construye el contexto para el template"""
        return self.context_builder_service.build_form_context(request, organization, form)
    
    def send_success_notification(self, request, message: str) -> None:
        """Envía notificación de éxito"""
        self.notification_service.send_success_message(request, message)
    
    def send_error_notification(self, request, message: str) -> None:
        """Envía notificación de error"""
        self.notification_service.send_error_message(request, message)
