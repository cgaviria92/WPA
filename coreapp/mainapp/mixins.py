"""
Mixins para vistas basadas en clases
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied

from .models import Organization, DynamicForm
from .services import OrganizationService, CoinService, ServiceError, PermissionError


class OrganizationRequiredMixin(LoginRequiredMixin):
    """Mixin que requiere acceso a una organización específica"""
    
    def dispatch(self, request, *args, **kwargs):
        self.org_slug = kwargs.get('org_slug')
        if not self.org_slug:
            messages.error(request, 'Organización no especificada')
            return redirect('mainapp:select_organization')
        
        try:
            self.org_service = OrganizationService(request.user, request)
            self.organization, self.membership = self.org_service.get_user_organization(self.org_slug)
        except PermissionError as e:
            messages.error(request, str(e))
            return redirect('mainapp:select_organization')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) if hasattr(super(), 'get_context_data') else {}
        context.update({
            'organization': self.organization,
            'membership': self.membership,
            'user_coins': self.request.user.monedas,
            'org_service': self.org_service,
        })
        return context


class AdminRequiredMixin:
    """Mixin que requiere permisos de administrador en la organización"""
    
    def dispatch(self, request, *args, **kwargs):
        # Debe usarse junto con OrganizationRequiredMixin
        if not hasattr(self, 'membership'):
            raise AttributeError('AdminRequiredMixin requiere OrganizationRequiredMixin')
        
        if not self.membership.is_admin:
            messages.error(request, 'No tienes permisos de administrador en esta organización')
            return redirect('mainapp:dashboard', org_slug=self.org_slug)
        
        return super().dispatch(request, *args, **kwargs)


class FormOwnerRequiredMixin:
    """Mixin que requiere ser propietario o admin del formulario"""
    
    def dispatch(self, request, *args, **kwargs):
        form_id = kwargs.get('form_id')
        if not form_id:
            raise Http404('Formulario no especificado')
        
        # Debe usarse junto con OrganizationRequiredMixin
        if not hasattr(self, 'organization'):
            raise AttributeError('FormOwnerRequiredMixin requiere OrganizationRequiredMixin')
        
        try:
            self.form = get_object_or_404(
                DynamicForm,
                id=form_id,
                organization=self.organization
            )
            
            # Verificar permisos
            if not (self.form.created_by == request.user or self.membership.is_admin):
                messages.error(request, 'No tienes permisos para acceder a este formulario')
                return redirect('mainapp:dashboard', org_slug=self.org_slug)
                
        except DynamicForm.DoesNotExist:
            raise Http404('Formulario no encontrado')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) if hasattr(super(), 'get_context_data') else {}
        context['form'] = self.form
        return context


class CoinRequiredMixin:
    """Mixin que verifica si el usuario tiene suficientes monedas"""
    required_coins = 0  # Debe ser sobrescrito en la vista
    
    def dispatch(self, request, *args, **kwargs):
        self.coin_service = CoinService(request.user, request)
        
        if hasattr(self, 'get_required_coins'):
            required = self.get_required_coins()
        else:
            required = self.required_coins
        
        if not self.coin_service.check_balance(required):
            messages.error(
                request,
                f'No tienes suficientes monedas. Necesitas {required}, '
                f'pero solo tienes {request.user.monedas}.'
            )
            return self.handle_insufficient_coins(request, *args, **kwargs)
        
        return super().dispatch(request, *args, **kwargs)
    
    def handle_insufficient_coins(self, request, *args, **kwargs):
        """Maneja cuando no hay suficientes monedas"""
        return redirect('mainapp:dashboard')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) if hasattr(super(), 'get_context_data') else {}
        context['coin_service'] = self.coin_service
        return context


class AjaxResponseMixin:
    """Mixin para manejar respuestas AJAX"""
    
    def dispatch(self, request, *args, **kwargs):
        self.is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        if self.is_ajax:
            data = {
                'success': True,
                'message': getattr(self, 'success_message', 'Operación exitosa'),
                'redirect_url': response.url if hasattr(response, 'url') else None
            }
            return JsonResponse(data)
        
        return response
    
    def form_invalid(self, form):
        response = super().form_invalid(form)
        
        if self.is_ajax:
            data = {
                'success': False,
                'errors': form.errors,
                'message': 'Error en el formulario'
            }
            return JsonResponse(data, status=400)
        
        return response


class ServiceMixin:
    """Mixin que proporciona servicios comunes"""
    
    def get_coin_service(self):
        if not hasattr(self, '_coin_service'):
            self._coin_service = CoinService(self.request.user, self.request)
        return self._coin_service
    
    def get_org_service(self):
        if not hasattr(self, '_org_service'):
            self._org_service = OrganizationService(self.request.user, self.request)
        return self._org_service
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) if hasattr(super(), 'get_context_data') else {}
        context.update({
            'coin_service': self.get_coin_service(),
            'org_service': self.get_org_service(),
        })
        return context


@method_decorator(csrf_exempt, name='dispatch')
class CSRFExemptMixin:
    """Mixin para eximir de CSRF (usar con cuidado)"""
    pass


class PermissionRequiredMixin:
    """Mixin que requiere permisos específicos en la organización"""
    required_permission = None  # Debe ser sobrescrito
    
    def dispatch(self, request, *args, **kwargs):
        # Debe usarse junto con OrganizationRequiredMixin
        if not hasattr(self, 'org_service'):
            raise AttributeError('PermissionRequiredMixin requiere OrganizationRequiredMixin')
        
        permission = self.get_required_permission()
        if not permission:
            raise AttributeError('required_permission debe ser definido')
        
        try:
            self.org_service.check_permission(self.organization, permission)
        except PermissionError as e:
            messages.error(request, str(e))
            return redirect('mainapp:dashboard', org_slug=self.org_slug)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_required_permission(self):
        """Obtiene el permiso requerido"""
        return self.required_permission


class MessageMixin:
    """Mixin para mensajes estandarizados"""
    success_message = None
    error_message = None
    
    def get_success_message(self, form=None):
        return self.success_message
    
    def get_error_message(self, form=None):
        return self.error_message
    
    def form_valid(self, form):
        response = super().form_valid(form)
        success_message = self.get_success_message(form)
        if success_message:
            messages.success(self.request, success_message)
        return response
    
    def form_invalid(self, form):
        response = super().form_invalid(form)
        error_message = self.get_error_message(form)
        if error_message:
            messages.error(self.request, error_message)
        return response


class BreadcrumbMixin:
    """Mixin para manejar breadcrumbs"""
    breadcrumbs = []
    
    def get_breadcrumbs(self):
        """Obtiene los breadcrumbs para la vista"""
        breadcrumbs = []
        
        # Breadcrumb base de organización
        if hasattr(self, 'organization'):
            breadcrumbs.extend([
                {'title': 'Organizaciones', 'url': 'mainapp:select_organization'},
                {'title': self.organization.name, 'url': 'mainapp:dashboard', 'url_args': [self.org_slug]},
            ])
        
        # Breadcrumbs específicos de la vista
        breadcrumbs.extend(self.breadcrumbs)
        
        return breadcrumbs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs) if hasattr(super(), 'get_context_data') else {}
        context['breadcrumbs'] = self.get_breadcrumbs()
        return context


class PaginationMixin:
    """Mixin para paginación estandarizada"""
    paginate_by = 20
    page_kwarg = 'page'
    
    def get_paginate_by(self, queryset):
        return self.paginate_by
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if 'page_obj' in context:
            # Agregar información útil de paginación
            page_obj = context['page_obj']
            context.update({
                'pagination_info': {
                    'has_previous': page_obj.has_previous(),
                    'has_next': page_obj.has_next(),
                    'previous_page_number': page_obj.previous_page_number() if page_obj.has_previous() else None,
                    'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
                    'current_page': page_obj.number,
                    'total_pages': page_obj.paginator.num_pages,
                    'total_items': page_obj.paginator.count,
                    'items_per_page': page_obj.paginator.per_page,
                }
            })
        
        return context
