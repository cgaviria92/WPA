"""
Interfaces para aplicar principios SOLID en WPA
Definición de contratos claros para servicios
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from django.contrib.auth.models import User
from django.http import HttpRequest


class IPermissionService(ABC):
    """Interface para servicios de permisos"""
    
    @abstractmethod
    def has_form_access(self, user: User, organization, form) -> bool:
        """Verifica si un usuario tiene acceso a un formulario"""
        pass
    
    @abstractmethod
    def can_edit_form(self, user: User, organization, form) -> bool:
        """Verifica si un usuario puede editar un formulario"""
        pass
    
    @abstractmethod
    def get_user_membership(self, user: User, organization):
        """Obtiene la membresía de un usuario en una organización"""
        pass


class IFormValidationService(ABC):
    """Interface para validación de formularios"""
    
    @abstractmethod
    def validate_form_submission(self, fields: List, request_data: Dict) -> Dict[str, Any]:
        """Valida los datos enviados en un formulario"""
        pass
    
    @abstractmethod
    def validate_field(self, field, value: Any) -> Dict[str, str]:
        """Valida un campo específico"""
        pass


class IFileProcessingService(ABC):
    """Interface para procesamiento de archivos"""
    
    @abstractmethod
    def validate_file(self, file, field) -> Dict[str, str]:
        """Valida un archivo subido"""
        pass
    
    @abstractmethod
    def calculate_file_cost(self, file, field) -> int:
        """Calcula el costo de un archivo"""
        pass
    
    @abstractmethod
    def process_file_upload(self, file, field, organization) -> Dict[str, Any]:
        """Procesa la subida de un archivo"""
        pass


class IFormSubmissionService(ABC):
    """Interface para manejo de envíos de formularios"""
    
    @abstractmethod
    def create_submission(self, form, data: Dict, user: Optional[User] = None) -> Any:
        """Crea un nuevo envío de formulario"""
        pass
    
    @abstractmethod
    def process_business_logic(self, form, submission_data: Dict) -> Dict[str, Any]:
        """Procesa la lógica de negocio del formulario"""
        pass


class IContextBuilderService(ABC):
    """Interface para construcción de contexto de templates"""
    
    @abstractmethod
    def build_form_context(self, request: HttpRequest, organization, form) -> Dict[str, Any]:
        """Construye el contexto para el template de formulario"""
        pass
    
    @abstractmethod
    def build_dashboard_context(self, request: HttpRequest, organization) -> Dict[str, Any]:
        """Construye el contexto para el dashboard"""
        pass


class INotificationService(ABC):
    """Interface para notificaciones"""
    
    @abstractmethod
    def send_success_message(self, request: HttpRequest, message: str) -> None:
        """Envía un mensaje de éxito"""
        pass
    
    @abstractmethod
    def send_error_message(self, request: HttpRequest, message: str) -> None:
        """Envía un mensaje de error"""
        pass
    
    @abstractmethod
    def send_warning_message(self, request: HttpRequest, message: str) -> None:
        """Envía un mensaje de advertencia"""
        pass
