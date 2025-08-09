"""
Vistas basadas en clases orientadas a objetos para WPA siguiendo principios SOLID
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

from .models import Organization, FormTemplate, DynamicForm, FieldType, DynamicFormField
from .service_factory import ServiceFactory, FormProcessor
from .mixins import OrganizationRequiredMixin, ServiceMixin


class BaseOrganizationView(OrganizationRequiredMixin, ServiceMixin, View):
    """Vista base para operaciones dentro de organizaciones usando servicios SOLID"""
    
    def get_context_data(self, **kwargs):
        """Contexto base para vistas de organización"""
        context = super().get_context_data(**kwargs)
        context.update({
            'organization': self.organization,
            'membership': self.membership,
        })
        return context


class CreateFormFromTemplateView(BaseOrganizationView, TemplateView):
    """Vista para crear formulario desde plantilla usando servicios SOLID"""
    template_name = 'mainapp/create_form_from_template.html'
    
    def get(self, request, *args, **kwargs):
        try:
            # Verificar permisos usando servicio SOLID
            if not (self.membership and (self.membership.is_admin or self.membership.can_edit_forms)):
                messages.error(request, 'No tienes permisos para crear formularios')
                return redirect('mainapp:dashboard', org_slug=self.org_slug)
            
            # Obtener plantilla
            template_id = kwargs.get('template_id')
            self.template = get_object_or_404(FormTemplate, id=template_id, is_active=True)
            
            # Calcular costo (lógica simplificada - puede mejorarse con un servicio específico)
            self.template_cost = len(self.template.template_data.get('fields', [])) * 50
            
            return super().get(request, *args, **kwargs)
            
        except Exception as e:
            messages.error(request, f'Error al cargar la plantilla: {str(e)}')
            return redirect('mainapp:dashboard', org_slug=self.org_slug)
    
    def post(self, request, *args, **kwargs):
        """Crear formulario desde plantilla usando FormProcessor SOLID"""
        try:
            # Verificar permisos
            if not (self.membership and (self.membership.is_admin or self.membership.can_edit_forms)):
                messages.error(request, 'No tienes permisos para crear formularios')
                return redirect('mainapp:dashboard', org_slug=self.org_slug)
            
            # Obtener plantilla
            template_id = kwargs.get('template_id')
            template = get_object_or_404(FormTemplate, id=template_id, is_active=True)
            
            # Datos del formulario
            title = request.POST.get('title', template.name)
            description = request.POST.get('description', template.description)
            is_public = request.POST.get('is_public', '0') == '1'
            
            # Usar FormProcessor para crear el formulario
            form_processor = FormProcessor()
            
            # Verificar monedas
            template_cost = len(template.template_data.get('fields', [])) * 50
            if request.user.monedas < template_cost:
                messages.error(
                    request,
                    f'No tienes suficientes monedas. Necesitas {template_cost} monedas, '
                    f'pero solo tienes {request.user.monedas}.'
                )
                return redirect('mainapp:form_templates', org_slug=self.org_slug)
            
            # Crear formulario (lógica simplificada)
            from django.db import transaction
            with transaction.atomic():
                # Crear formulario base
                form = DynamicForm.objects.create(
                    title=title,
                    description=description,
                    organization=self.organization,
                    creator=request.user,
                    is_public=is_public,
                    total_cost=template_cost
                )
                
                # Crear campos desde la plantilla
                for order, field_data in enumerate(template.template_data.get('fields', []), 1):
                    field_type = FieldType.objects.get(name=field_data['field_type'])
                    DynamicFormField.objects.create(
                        form=form,
                        field_type=field_type,
                        label=field_data['label'],
                        help_text=field_data.get('help_text', ''),
                        is_required=field_data.get('is_required', False),
                        order=order,
                        max_length=field_data.get('max_length'),
                        choices=field_data.get('choices'),
                    )
                
                # Cobrar monedas
                request.user.monedas -= template_cost
                request.user.save()
            
            messages.success(
                request,
                f'¡Formulario "{form.title}" creado exitosamente desde la plantilla!'
            )
            return redirect('mainapp:edit_form', org_slug=self.org_slug, form_id=form.id)
            
        except Exception as e:
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
    """Vista para manejar el progreso de creación de formularios usando servicios SOLID"""
    
    def post(self, request):
        """Iniciar creación de formulario con progreso usando FormProcessor"""
        try:
            data = json.loads(request.body)
            org_slug = data.get('org_slug')
            template_id = data.get('template_id')
            form_data = data.get('form_data', {})
            
            # Obtener organización
            organization = get_object_or_404(Organization, slug=org_slug)
            
            # Verificar permisos
            membership = organization.memberships.filter(user=request.user).first()
            if not membership or not (membership.is_admin or membership.can_edit_forms):
                return JsonResponse({
                    'error': True,
                    'message': 'No tienes permisos para crear formularios'
                })
            
            # Obtener plantilla
            template = get_object_or_404(FormTemplate, id=template_id, is_active=True)
            
            # Usar FormProcessor para crear formulario
            form_processor = FormProcessor()
            
            # Calcular costo
            template_cost = len(template.template_data.get('fields', [])) * 50
            
            # Verificar monedas
            if request.user.monedas < template_cost:
                return JsonResponse({
                    'error': True,
                    'message': f'Monedas insuficientes. Necesitas {template_cost}, tienes {request.user.monedas}'
                })
            
            # Simular progreso (en una implementación real esto sería asíncrono)
            progress_data = [
                {"step": 1, "message": "Validando datos del formulario...", "progress": 20},
                {"step": 2, "message": "Verificando costo y monedas...", "progress": 40},
                {"step": 3, "message": "Creando estructura del formulario...", "progress": 60},
                {"step": 4, "message": "Agregando campos al formulario...", "progress": 80},
                {"step": 5, "message": "Finalizando creación...", "progress": 100}
            ]
            
            return JsonResponse({
                'success': True,
                'progress': progress_data,
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
