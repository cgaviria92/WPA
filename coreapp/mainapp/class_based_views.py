"""
Vistas basadas en clases orientadas a objetos para WPA
"""

from django.views.generic import View, TemplateView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from django.db import models
import json

from .models import Organization, FormTemplate, DynamicForm, FieldType
from .services import (
    FormService, OrganizationService, CoinService, ProgressTracker,
    ServiceError, InsufficientCoinsError, PermissionError
)


class BaseOrganizationView(LoginRequiredMixin, View):
    """Vista base para operaciones dentro de organizaciones"""
    
    def dispatch(self, request, *args, **kwargs):
        self.org_slug = kwargs.get('org_slug')
        try:
            self.org_service = OrganizationService(request.user, request)
            self.organization, self.membership = self.org_service.get_user_organization(self.org_slug)
        except PermissionError as e:
            messages.error(request, str(e))
            return redirect('mainapp:select_organization')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Contexto base para vistas de organización"""
        return {
            'organization': self.organization,
            'membership': self.membership,
            'user_coins': self.request.user.monedas,
            **kwargs
        }


class CreateFormFromTemplateView(BaseOrganizationView, TemplateView):
    """Vista para crear formulario desde plantilla"""
    template_name = 'mainapp/create_form_from_template.html'
    
    def get(self, request, *args, **kwargs):
        try:
            # Verificar permisos
            self.org_service.check_permission(self.organization, 'edit_forms')
            
            # Obtener plantilla
            template_id = kwargs.get('template_id')
            self.template = get_object_or_404(FormTemplate, id=template_id, is_active=True)
            
            # Calcular costo
            self.form_service = FormService(request.user, request)
            self.template_cost = self.form_service.calculate_template_cost(self.template)
            
            return super().get(request, *args, **kwargs)
            
        except PermissionError as e:
            messages.error(request, str(e))
            return redirect('mainapp:dashboard', org_slug=self.org_slug)
    
    def post(self, request, *args, **kwargs):
        """Crear formulario desde plantilla"""
        try:
            # Verificar permisos
            self.org_service.check_permission(self.organization, 'edit_forms')
            
            # Obtener plantilla y datos del formulario
            template_id = kwargs.get('template_id')
            template = get_object_or_404(FormTemplate, id=template_id, is_active=True)
            
            title = request.POST.get('title', template.name)
            description = request.POST.get('description', template.description)
            is_public = request.POST.get('is_public', '0') == '1'
            
            # Crear formulario usando el servicio
            form_service = FormService(request.user, request)
            form = form_service.create_form_from_template(
                organization=self.organization,
                template=template,
                title=title,
                description=description,
                is_public=is_public
            )
            
            messages.success(
                request,
                f'¡Formulario "{form.title}" creado exitosamente desde la plantilla!'
            )
            return redirect('mainapp:edit_form', org_slug=self.org_slug, form_id=form.id)
            
        except InsufficientCoinsError as e:
            messages.error(
                request,
                f'No tienes suficientes monedas. Necesitas {e.required} monedas, '
                f'pero solo tienes {e.available}.'
            )
            return redirect('mainapp:form_templates', org_slug=self.org_slug)
            
        except PermissionError as e:
            messages.error(request, str(e))
            return redirect('mainapp:dashboard', org_slug=self.org_slug)
            
        except ServiceError as e:
            messages.error(request, f'Error al crear el formulario: {str(e)}')
            return redirect('mainapp:form_templates', org_slug=self.org_slug)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'template': self.template,
            'template_cost': self.template_cost,
            'can_afford': self.request.user.monedas >= self.template_cost,
        })
        return context


@method_decorator(csrf_exempt, name='dispatch')
class FormCreationProgressView(LoginRequiredMixin, View):
    """Vista para manejar el progreso de creación de formularios"""
    
    def post(self, request):
        """Iniciar creación de formulario con progreso"""
        try:
            data = json.loads(request.body)
            org_slug = data.get('org_slug')
            template_id = data.get('template_id')
            form_data = data.get('form_data', {})
            
            # Verificar organización y permisos
            org_service = OrganizationService(request.user, request)
            organization, membership = org_service.get_user_organization(org_slug)
            org_service.check_permission(organization, 'edit_forms')
            
            # Iniciar tracker de progreso
            progress = ProgressTracker(total_steps=5)
            
            # Paso 1: Validar datos
            progress.update(1, "Validando datos del formulario...")
            
            template = get_object_or_404(FormTemplate, id=template_id, is_active=True)
            form_service = FormService(request.user, request)
            
            # Paso 2: Verificar costo
            progress.update(2, "Verificando costo y monedas...")
            template_cost = form_service.calculate_template_cost(template)
            
            if not form_service.coin_service.check_balance(template_cost):
                return JsonResponse({
                    'error': True,
                    'message': f'Monedas insuficientes. Necesitas {template_cost}, tienes {request.user.monedas}'
                })
            
            # Paso 3: Crear formulario
            progress.update(3, "Creando estructura del formulario...")
            
            # Paso 4: Crear campos
            progress.update(4, "Agregando campos al formulario...")
            
            # Paso 5: Finalizar
            progress.update(5, "Finalizando creación...")
            
            # En una implementación real, aquí se ejecutaría la creación
            # Por ahora, devolvemos el progreso completo
            
            return JsonResponse({
                'success': True,
                'progress': progress.get_progress_data(),
                'redirect_url': f'/org/{org_slug}/forms/',
                'message': 'Formulario creado exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({
                'error': True,
                'message': f'Error durante la creación: {str(e)}'
            })
    
    def get(self, request):
        """Obtener progreso de una tarea"""
        task_id = request.GET.get('task_id')
        
        if not task_id:
            return JsonResponse({'error': 'Task ID requerido'})
        
        # Simular progreso (en producción usaría Celery o similar)
        import random
        progress_data = {
            'current_step': random.randint(1, 5),
            'total_steps': 5,
            'percentage': random.randint(20, 95),
            'message': 'Procesando formulario...',
            'completed': False
        }
        
        return JsonResponse(progress_data)


class FormAnalyticsView(BaseOrganizationView, TemplateView):
    """Vista para analíticas de formularios"""
    template_name = 'mainapp/form_analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener estadísticas
        forms = DynamicForm.objects.filter(organization=self.organization, is_active=True)
        
        analytics_data = {
            'total_forms': forms.count(),
            'total_submissions': sum(form.submissions.count() for form in forms),
            'total_cost_spent': sum(form.total_cost for form in forms),
            'average_cost_per_form': forms.aggregate(
                avg_cost=models.Avg('total_cost')
            )['avg_cost'] or 0,
            'most_used_field_types': self._get_most_used_field_types(),
            'submission_trends': self._get_submission_trends(),
        }
        
        context['analytics'] = analytics_data
        return context
    
    def _get_most_used_field_types(self):
        """Obtener tipos de campo más utilizados"""
        from django.db.models import Count
        from .models import DynamicFormField
        
        return DynamicFormField.objects.filter(
            form__organization=self.organization,
            form__is_active=True
        ).values(
            'field_type__display_name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]
    
    def _get_submission_trends(self):
        """Obtener tendencias de envíos"""
        from django.db.models import Count
        from django.db.models.functions import TruncDay
        from .models import FormSubmission
        
        return FormSubmission.objects.filter(
            form__organization=self.organization
        ).annotate(
            day=TruncDay('submitted_at')
        ).values('day').annotate(
            count=Count('id')
        ).order_by('day')[-30:]  # Últimos 30 días
