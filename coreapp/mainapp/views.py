from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.text import slugify
from django.db import transaction
from django.db import models
from .models import (
    CustomUser, Organization, OrganizationMembership, FieldType, 
    DynamicForm, DynamicFormField, FormSubmission, CoinTransaction, ActivityLog,
    FormTemplate, InventoryItem, InventoryTransaction, BusinessLogicProcessor
)
from .forms import (
    DynamicFormCreationForm, DynamicFormFieldForm, UserRegistrationForm,
    OrganizationCreationForm, UserInvitationForm, BulkUserInviteForm
)
import json

def get_client_ip(request):
    """Obtener IP del cliente"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def log_activity(user, action, description, organization=None, form=None, request=None):
    """Crear log de actividad"""
    ActivityLog.objects.create(
        user=user,
        organization=organization,
        action=action,
        description=description,
        related_form=form,
        ip_address=get_client_ip(request) if request else None,
        user_agent=request.META.get('HTTP_USER_AGENT', '') if request else ''
    )

def index(request):
    """Página principal - Muestra formularios públicos de todas las organizaciones"""
    public_forms = DynamicForm.objects.filter(is_active=True, is_public=True).order_by('-created_at')
    
    context = {
        'forms': public_forms,
        'total_organizations': Organization.objects.filter(is_active=True).count(),
        'total_forms': DynamicForm.objects.filter(is_active=True).count(),
        'total_users': CustomUser.objects.count(),
    }
    return render(request, 'mainapp/index.html', context)

def register(request):
    """Registro de usuarios"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = form.save()
                    login(request, user)
                    
                    # Log de registro
                    log_activity(user, 'login', f'Usuario registrado: {user.username}', request=request)
                    
                    messages.success(request, 'Registro exitoso. ¡Bienvenido al sistema!')
                    return redirect('mainapp:select_organization')
            except Exception as e:
                messages.error(request, f'Error durante el registro: {str(e)}')
                return render(request, 'registration/register.html', {'form': form})
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
@login_required
def select_organization(request):
    """Seleccionar organización o crear nueva"""
    try:
        user_memberships = request.user.memberships.filter(
            is_active=True,
            organization__is_active=True,
            organization__slug__isnull=False
        ).select_related('organization')
    except Exception as e:
        # En caso de error, crear una lista vacía
        user_memberships = []
    
    context = {
        'user_memberships': user_memberships,
    }
    return render(request, 'mainapp/select_organization.html', context)

@login_required
def create_organization(request):
    """Crear nueva organización"""
    if request.method == 'POST':
        form = OrganizationCreationForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                # Crear organización
                organization = form.save(commit=False)
                organization.owner = request.user
                organization.slug = slugify(organization.name)
                organization.save()
                
                # Crear membresía del propietario
                OrganizationMembership.objects.create(
                    user=request.user,
                    organization=organization,
                    role='owner',
                    invited_by=request.user
                )
                
                # Log de actividad
                log_activity(
                    request.user, 'create_organization', 
                    f'Organización creada: {organization.name}',
                    organization=organization, request=request
                )
                
                messages.success(request, f'Organización "{organization.name}" creada exitosamente.')
                return redirect('mainapp:dashboard', org_slug=organization.slug)
    else:
        form = OrganizationCreationForm()
    
    return render(request, 'mainapp/create_organization.html', {'form': form})

@login_required
def dashboard(request, org_slug):
    """Dashboard de la organización"""
    organization = get_object_or_404(Organization, slug=org_slug, is_active=True)
    
    # Verificar que el usuario pertenece a la organización
    try:
        membership = OrganizationMembership.objects.get(
            user=request.user, 
            organization=organization, 
            is_active=True
        )
    except OrganizationMembership.DoesNotExist:
        messages.error(request, 'No tienes acceso a esta organización.')
        return redirect('mainapp:select_organization')
    
    # Obtener datos del dashboard
    org_forms = organization.forms.filter(is_active=True).order_by('-created_at')
    recent_submissions = FormSubmission.objects.filter(
        form__organization=organization
    ).order_by('-submitted_at')[:10]
    
    recent_activities = organization.activity_logs.all()[:10]
    team_members = organization.memberships.filter(is_active=True).order_by('-joined_at')
    
    # Estadísticas
    stats = {
        'total_forms': org_forms.count(),
        'total_submissions': FormSubmission.objects.filter(form__organization=organization).count(),
        'total_members': team_members.count(),
        'total_cost': sum(form.total_cost for form in org_forms),
    }
    
    context = {
        'organization': organization,
        'membership': membership,
        'org_forms': org_forms,
        'recent_submissions': recent_submissions,
        'recent_activities': recent_activities,
        'team_members': team_members,
        'stats': stats,
        'available_field_types': FieldType.objects.all(),
    }
    return render(request, 'mainapp/dashboard.html', context)

@login_required
def create_form(request, org_slug):
    """Crear nuevo formulario dinámico"""
    organization = get_object_or_404(Organization, slug=org_slug, is_active=True)
    
    # Verificar permisos
    try:
        membership = OrganizationMembership.objects.get(
            user=request.user, organization=organization, is_active=True
        )
        if not membership.can_edit_forms():
            messages.error(request, 'No tienes permisos para crear formularios.')
            return redirect('mainapp:dashboard', org_slug=org_slug)
    except OrganizationMembership.DoesNotExist:
        messages.error(request, 'No tienes acceso a esta organización.')
        return redirect('mainapp:select_organization')
    
    if request.method == 'POST':
        form = DynamicFormCreationForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                dynamic_form = form.save(commit=False)
                dynamic_form.organization = organization
                dynamic_form.creator = request.user
                dynamic_form.save()
                
                # Log de actividad
                log_activity(
                    request.user, 'create_form',
                    f'Formulario creado: {dynamic_form.title}',
                    organization=organization, form=dynamic_form, request=request
                )
                
                messages.success(request, 'Formulario creado exitosamente.')
                return redirect('mainapp:edit_form', org_slug=org_slug, form_id=dynamic_form.id)
    else:
        form = DynamicFormCreationForm()
    
    context = {
        'form': form,
        'organization': organization,
        'membership': membership,
    }
    return render(request, 'mainapp/create_form.html', context)

@login_required
def edit_form(request, org_slug, form_id):
    """Editar formulario dinámico"""
    organization = get_object_or_404(Organization, slug=org_slug, is_active=True)
    dynamic_form = get_object_or_404(DynamicForm, id=form_id, organization=organization)
    
    # Verificar permisos
    try:
        membership = OrganizationMembership.objects.get(
            user=request.user, organization=organization, is_active=True
        )
        if not membership.can_edit_forms():
            messages.error(request, 'No tienes permisos para editar formularios.')
            return redirect('mainapp:dashboard', org_slug=org_slug)
    except OrganizationMembership.DoesNotExist:
        messages.error(request, 'No tienes acceso a esta organización.')
        return redirect('mainapp:select_organization')
    
    fields = dynamic_form.fields.all().order_by('order')
    field_types = FieldType.objects.all()
    
    # Si no hay tipos de campo, mostrar mensaje de error
    if not field_types.exists():
        messages.error(request, 
            'No hay tipos de campo disponibles. Contacta al administrador para configurar el sistema.')
    
    context = {
        'organization': organization,
        'membership': membership,
        'dynamic_form': dynamic_form,
        'fields': fields,
        'field_types': field_types,
        'has_field_types': field_types.exists(),
    }
    return render(request, 'mainapp/edit_form.html', context)

# ... (continúo con el resto de las vistas en el siguiente bloque)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def add_field_to_form(request, org_slug, form_id):
    """Agregar campo a formulario (AJAX)"""
    organization = get_object_or_404(Organization, slug=org_slug, is_active=True)
    dynamic_form = get_object_or_404(DynamicForm, id=form_id, organization=organization)
    
    # Verificar permisos
    try:
        membership = OrganizationMembership.objects.get(
            user=request.user, organization=organization, is_active=True
        )
        if not membership.can_edit_forms():
            return JsonResponse({'success': False, 'error': 'Sin permisos para editar formularios'})
    except OrganizationMembership.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Sin acceso a esta organización'})
    
    try:
        data = json.loads(request.body)
        field_type_id = data.get('field_type_id')
        label = data.get('label')
        is_required = data.get('is_required', False)
        help_text = data.get('help_text', '')
        choices = data.get('choices', '')
        
        field_type = get_object_or_404(FieldType, id=field_type_id)
        
        # Verificar si el usuario puede costear el campo
        if request.user.monedas < field_type.cost:
            return JsonResponse({
                'success': False,
                'error': f'No tienes suficientes monedas. Necesitas {field_type.cost} monedas.'
            })
        
        with transaction.atomic():
            # Crear el campo
            field = DynamicFormField.objects.create(
                form=dynamic_form,
                field_type=field_type,
                label=label,
                is_required=is_required,
                help_text=help_text,
                choices=choices,
                order=dynamic_form.fields.count()
            )
            
            # Cobrar las monedas
            request.user.monedas -= field_type.cost
            request.user.save()
            
            # Registrar la transacción
            CoinTransaction.objects.create(
                user=request.user,
                organization=organization,
                transaction_type='spend',
                amount=field_type.cost,
                description=f'Campo agregado: {label} ({field_type.display_name})',
                related_form=dynamic_form
            )
            
            # Actualizar costo total del formulario
            dynamic_form.total_cost = dynamic_form.calculate_total_cost()
            dynamic_form.save()
            
            # Log de actividad
            log_activity(
                request.user, 'add_field',
                f'Campo agregado: {label} en {dynamic_form.title}',
                organization=organization, form=dynamic_form, request=request
            )
        
        return JsonResponse({
            'success': True,
            'field_id': field.id,
            'remaining_coins': request.user.monedas
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def delete_field(request, org_slug, field_id):
    """Eliminar campo de formulario"""
    organization = get_object_or_404(Organization, slug=org_slug, is_active=True)
    field = get_object_or_404(DynamicFormField, id=field_id, form__organization=organization)
    
    # Verificar permisos
    try:
        membership = OrganizationMembership.objects.get(
            user=request.user, organization=organization, is_active=True
        )
        if not membership.can_edit_forms():
            messages.error(request, 'No tienes permisos para eliminar campos.')
            return redirect('mainapp:dashboard', org_slug=org_slug)
    except OrganizationMembership.DoesNotExist:
        messages.error(request, 'No tienes acceso a esta organización.')
        return redirect('mainapp:select_organization')
    
    form_id = field.form.id
    
    with transaction.atomic():
        # Reembolsar monedas (50% del costo original)
        refund_amount = field.field_type.cost // 2
        request.user.monedas += refund_amount
        request.user.save()
        
        # Registrar transacción de reembolso
        CoinTransaction.objects.create(
            user=request.user,
            organization=organization,
            transaction_type='refund',
            amount=refund_amount,
            description=f'Reembolso por eliminar campo: {field.label}',
            related_form=field.form
        )
        
        # Log de actividad
        log_activity(
            request.user, 'remove_field',
            f'Campo eliminado: {field.label} de {field.form.title}',
            organization=organization, form=field.form, request=request
        )
        
        field.delete()
        
        # Actualizar costo total del formulario
        dynamic_form = field.form
        dynamic_form.total_cost = dynamic_form.calculate_total_cost()
        dynamic_form.save()
    
    messages.success(request, f'Campo eliminado. Reembolso: {refund_amount} monedas.')
    return redirect('mainapp:edit_form', org_slug=org_slug, form_id=form_id)

def view_form(request, org_slug, form_id):
    """Ver y enviar datos a un formulario público"""
    organization = get_object_or_404(Organization, slug=org_slug, is_active=True)
    dynamic_form = get_object_or_404(DynamicForm, id=form_id, organization=organization, is_active=True)
    
    # Verificar si el formulario es público o el usuario tiene acceso
    has_access = dynamic_form.is_public
    if not has_access and request.user.is_authenticated:
        try:
            membership = OrganizationMembership.objects.get(
                user=request.user, organization=organization, is_active=True
            )
            has_access = True
        except OrganizationMembership.DoesNotExist:
            pass
    
    if not has_access:
        messages.error(request, 'No tienes acceso a este formulario.')
        return redirect('mainapp:index')
    
    fields = dynamic_form.fields.all().order_by('order')
    
    if request.method == 'POST':
        submission_data = {}
        valid = True
        errors = {}
        total_file_cost = 0
        uploaded_files = []
        
        for field in fields:
            field_name = f'field_{field.id}'
            
            # Manejar campos de archivo
            if field.field_type.name == 'file':
                uploaded_file = request.FILES.get(field_name)
                
                if field.is_required and not uploaded_file:
                    valid = False
                    errors[field_name] = 'Este campo es obligatorio'
                elif uploaded_file:
                    # Validar tamaño del archivo
                    if not field.validate_file_size(uploaded_file.size):
                        valid = False
                        max_mb = field.max_file_size_mb or 5.0
                        current_mb = uploaded_file.size / (1024 * 1024)
                        errors[field_name] = f'Archivo demasiado grande ({current_mb:.1f} MB). Máximo: {max_mb} MB'
                    else:
                        # Validar tipo de archivo
                        import mimetypes
                        file_type = mimetypes.guess_type(uploaded_file.name)[0] or ''
                        file_ext = '.' + uploaded_file.name.split('.')[-1].lower() if '.' in uploaded_file.name else ''
                        allowed_types = field.get_allowed_file_types_list()
                        
                        type_allowed = False
                        for allowed in allowed_types:
                            if allowed.startswith('.'):  # Es una extensión
                                if file_ext == allowed.lower():
                                    type_allowed = True
                                    break
                            elif '/' in allowed:  # Es un tipo MIME
                                if allowed.endswith('/*'):  # Tipo general como image/*
                                    if file_type.startswith(allowed[:-1]):
                                        type_allowed = True
                                        break
                                elif file_type == allowed:  # Tipo específico
                                    type_allowed = True
                                    break
                        
                        if not type_allowed:
                            valid = False
                            allowed_display = ', '.join(allowed_types)
                            errors[field_name] = f'Tipo de archivo no permitido. Permitidos: {allowed_display}'
                        else:
                            # Calcular costo del archivo
                            file_cost = field.calculate_file_cost(uploaded_file.size)
                            total_file_cost += file_cost
                            
                            # Almacenar información del archivo para procesamiento posterior
                            uploaded_files.append({
                                'field': field,
                                'file': uploaded_file,
                                'cost': file_cost,
                                'file_type': file_type
                            })
                            
                            submission_data[field_name] = f"archivo_{uploaded_file.name}"
            else:
                # Manejar otros tipos de campo
                value = request.POST.get(field_name)
                
                if field.is_required and not value:
                    valid = False
                    errors[field_name] = 'Este campo es obligatorio'
                else:
                    submission_data[field_name] = value
        
        # Verificar si el usuario tiene suficientes monedas para los archivos
        if valid and total_file_cost > 0 and request.user.is_authenticated:
            if request.user.monedas < total_file_cost:
                valid = False
                errors['__all__'] = f'No tienes suficientes monedas para subir los archivos. Necesitas {total_file_cost} monedas, tienes {request.user.monedas}.'
        
        if valid:
            with transaction.atomic():
                # Guardar envío
                submission = FormSubmission.objects.create(
                    form=dynamic_form,
                    submitted_by=request.user if request.user.is_authenticated else None,
                    data=submission_data,
                    ip_address=get_client_ip(request)
                )
                
                # Procesar archivos subidos
                for file_info in uploaded_files:
                    from .models import UploadedFile
                    
                    uploaded_file_obj = UploadedFile.objects.create(
                        submission=submission,
                        field=file_info['field'],
                        file=file_info['file'],
                        original_name=file_info['file'].name,
                        file_size=file_info['file'].size,
                        mime_type=file_info['file_type'],
                        cost_charged=file_info['cost'],
                        uploaded_by=request.user if request.user.is_authenticated else None
                    )
                    
                    # Actualizar referencia en submission_data
                    field_name = f'field_{file_info["field"].id}'
                    submission_data[field_name] = uploaded_file_obj.file.url
                
                # Actualizar los datos del submission con las URLs de los archivos
                submission.data = submission_data
                submission.save()
                
                # Cobrar monedas por los archivos
                if total_file_cost > 0 and request.user.is_authenticated:
                    request.user.monedas -= total_file_cost
                    request.user.save()
                    
                    # Registrar transacción
                    from .models import CoinTransaction
                    CoinTransaction.objects.create(
                        user=request.user,
                        organization=organization,
                        transaction_type='spend',
                        amount=total_file_cost,
                        description=f'Subida de archivos en formulario: {dynamic_form.title}',
                        related_form=dynamic_form
                    )
                
                # Log de actividad
                if request.user.is_authenticated:
                    log_activity(
                        request.user, 'submit_form',
                        f'Formulario enviado: {dynamic_form.title}' + 
                        (f' (archivos: {len(uploaded_files)}, costo: {total_file_cost} monedas)' if uploaded_files else ''),
                        organization=organization, form=dynamic_form, request=request
                    )
                
            messages.success(request, 
                f'Formulario enviado exitosamente.' + 
                (f' Archivos subidos: {len(uploaded_files)}. Costo: {total_file_cost} monedas.' if uploaded_files else '')
            )
            return redirect('mainapp:form_success')
    
    context = {
        'organization': organization,
        'dynamic_form': dynamic_form,
        'fields': fields,
    }
    return render(request, 'mainapp/view_form.html', context)

def form_success(request):
    """Página de éxito después de enviar un formulario"""
    return render(request, 'mainapp/form_success.html')

@login_required
def form_submissions(request, org_slug, form_id):
    """Ver envíos de un formulario (solo miembros con permisos)"""
    organization = get_object_or_404(Organization, slug=org_slug, is_active=True)
    dynamic_form = get_object_or_404(DynamicForm, id=form_id, organization=organization)
    
    # Verificar permisos
    try:
        membership = OrganizationMembership.objects.get(
            user=request.user, organization=organization, is_active=True
        )
        if not membership.can_view_submissions():
            messages.error(request, 'No tienes permisos para ver las respuestas.')
            return redirect('mainapp:dashboard', org_slug=org_slug)
    except OrganizationMembership.DoesNotExist:
        messages.error(request, 'No tienes acceso a esta organización.')
        return redirect('mainapp:select_organization')
    
    submissions = dynamic_form.submissions.all().order_by('-submitted_at')
    fields = dynamic_form.fields.all().order_by('order')
    
    # DEBUG: Información de debug
    print(f"=== DEBUG form_submissions ===")
    print(f"Formulario ID: {form_id}")
    print(f"Organización: {organization.name}")
    print(f"Total submissions: {submissions.count()}")
    print(f"Campos del formulario:")
    for field in fields:
        print(f"  - Campo ID: {field.id}, Label: {field.label}, Order: {field.order}")
    
    print(f"Datos de submissions:")
    for i, submission in enumerate(submissions[:3]):  # Solo primeras 3
        print(f"  Submission {i+1}:")
        print(f"    ID: {submission.id}")
        print(f"    Usuario: {submission.submitted_by}")
        print(f"    Fecha: {submission.submitted_at}")
        print(f"    Datos: {submission.data}")
        print(f"    Tipo de datos: {type(submission.data)}")
        if isinstance(submission.data, dict):
            for key, value in submission.data.items():
                print(f"      {key}: {value}")
    print(f"=== FIN DEBUG ===")
    
    context = {
        'organization': organization,
        'membership': membership,
        'dynamic_form': dynamic_form,
        'submissions': submissions,
        'fields': fields,
    }
    return render(request, 'mainapp/form_submissions.html', context)

@login_required
def team_management(request, org_slug):
    """Gestión del equipo de la organización"""
    organization = get_object_or_404(Organization, slug=org_slug, is_active=True)
    
    # Verificar permisos
    try:
        membership = OrganizationMembership.objects.get(
            user=request.user, organization=organization, is_active=True
        )
        if not membership.can_manage_users():
            messages.error(request, 'No tienes permisos para gestionar usuarios.')
            return redirect('mainapp:dashboard', org_slug=org_slug)
    except OrganizationMembership.DoesNotExist:
        messages.error(request, 'No tienes acceso a esta organización.')
        return redirect('mainapp:select_organization')
    
    team_members = organization.memberships.filter(is_active=True).order_by('-joined_at')
    
    # Formularios para invitación
    invite_form = UserInvitationForm()
    bulk_invite_form = BulkUserInviteForm()
    
    context = {
        'organization': organization,
        'membership': membership,
        'members': team_members,
        'user_membership': membership,
        'invite_form': invite_form,
        'bulk_invite_form': bulk_invite_form,
    }
    return render(request, 'mainapp/team_management.html', context)

@login_required
def activity_logs(request, org_slug):
    """Ver logs de actividad de la organización"""
    organization = get_object_or_404(Organization, slug=org_slug, is_active=True)
    
    # Verificar permisos
    try:
        membership = OrganizationMembership.objects.get(
            user=request.user, organization=organization, is_active=True
        )
        if not membership.can_manage_users():
            messages.error(request, 'No tienes permisos para ver los logs.')
            return redirect('mainapp:dashboard', org_slug=org_slug)
    except OrganizationMembership.DoesNotExist:
        messages.error(request, 'No tienes acceso a esta organización.')
        return redirect('mainapp:select_organization')
    
    logs = organization.activity_logs.all().order_by('-created_at')
    
    # Filtros
    user_filter = request.GET.get('user')
    action_filter = request.GET.get('action')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if user_filter:
        logs = logs.filter(user_id=user_filter)
    if action_filter:
        logs = logs.filter(action=action_filter)
    if date_from:
        logs = logs.filter(created_at__date__gte=date_from)
    if date_to:
        logs = logs.filter(created_at__date__lte=date_to)
    
    # Estadísticas
    from django.db.models import Count
    from datetime import datetime, timedelta
    
    stats = {
        'total_logs': logs.count(),
        'forms_created': logs.filter(action='create_form').count(),
        'submissions_received': logs.filter(action='form_submission').count(),
        'users_active': logs.filter(
            created_at__gte=datetime.now() - timedelta(days=30)
        ).values('user').distinct().count(),
    }
    
    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(logs, 25)  # 25 logs por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'organization': organization,
        'membership': membership,
        'logs': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'members': organization.members.filter(is_active=True),
        'stats': stats,
    }
    return render(request, 'mainapp/activity_logs.html', context)


@login_required
@require_http_methods(["POST"])
def invite_user(request, org_slug):
    """Invitar usuario a la organización"""
    organization = get_object_or_404(Organization, slug=org_slug, is_active=True)
    
    # Verificar permisos
    try:
        membership = OrganizationMembership.objects.get(
            user=request.user, organization=organization, is_active=True
        )
        if not membership.can_manage_users():
            return JsonResponse({'success': False, 'error': 'Sin permisos'})
    except OrganizationMembership.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Sin acceso'})
    
    form = UserInvitationForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data['email']
        role = form.cleaned_data['role']
        
        # Verificar si el usuario ya existe
        try:
            invited_user = CustomUser.objects.get(email=email)
            # Verificar si ya es miembro
            if OrganizationMembership.objects.filter(
                user=invited_user, organization=organization, is_active=True
            ).exists():
                messages.error(request, f'{email} ya es miembro de esta organización.')
            else:
                # Agregar a la organización
                with transaction.atomic():
                    OrganizationMembership.objects.create(
                        user=invited_user,
                        organization=organization,
                        role=role,
                        invited_by=request.user
                    )
                    
                    # Log de actividad
                    log_activity(
                        user=request.user,
                        action='user_invited',
                        description=f'Usuario {email} invitado con rol {role}',
                        organization=organization,
                        request=request
                    )
                    
                    messages.success(request, f'Usuario {email} agregado exitosamente.')
        except CustomUser.DoesNotExist:
            messages.error(request, f'No existe un usuario con email {email}. El usuario debe registrarse primero.')
    
    return redirect('mainapp:team_management', org_slug=org_slug)


@login_required
@require_http_methods(["POST"])
def bulk_invite_users(request, org_slug):
    """Invitar múltiples usuarios a la organización"""
    organization = get_object_or_404(Organization, slug=org_slug, is_active=True)
    
    # Verificar permisos
    try:
        membership = OrganizationMembership.objects.get(
            user=request.user, organization=organization, is_active=True
        )
        if not membership.can_manage_users():
            return JsonResponse({'success': False, 'error': 'Sin permisos'})
    except OrganizationMembership.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Sin acceso'})
    
    users_data = request.POST.get('users_data', '')
    
    if not users_data:
        messages.error(request, 'No se proporcionaron datos de usuarios.')
        return redirect('mainapp:team_management', org_slug=org_slug)
    
    success_count = 0
    error_count = 0
    
    # Procesar datos: email1,role1;email2,role2
    for line in users_data.strip().split(';'):
        if not line.strip():
            continue
        
        try:
            parts = line.strip().split(',')
            if len(parts) != 2:
                error_count += 1
                continue
            
            email, role = parts[0].strip(), parts[1].strip()
            
            if role not in ['admin', 'editor', 'viewer']:
                error_count += 1
                continue
            
            # Verificar si el usuario existe
            try:
                invited_user = CustomUser.objects.get(email=email)
                # Verificar si ya es miembro
                if not OrganizationMembership.objects.filter(
                    user=invited_user, organization=organization, is_active=True
                ).exists():
                    OrganizationMembership.objects.create(
                        user=invited_user,
                        organization=organization,
                        role=role,
                        invited_by=request.user
                    )
                    success_count += 1
            except CustomUser.DoesNotExist:
                error_count += 1
        except Exception:
            error_count += 1
    
    # Log de actividad
    log_activity(
        user=request.user,
        action='bulk_invite',
        description=f'Invitación masiva: {success_count} exitosos, {error_count} errores',
        organization=organization,
        request=request
    )
    
    if success_count > 0:
        messages.success(request, f'{success_count} usuarios agregados exitosamente.')
    if error_count > 0:
        messages.warning(request, f'{error_count} usuarios no pudieron ser agregados.')
    
    return redirect('mainapp:team_management', org_slug=org_slug)


@login_required
@require_http_methods(["POST"])
def change_member_role(request, org_slug, membership_id):
    """Cambiar rol de un miembro"""
    organization = get_object_or_404(Organization, slug=org_slug, is_active=True)
    target_membership = get_object_or_404(OrganizationMembership, id=membership_id, organization=organization)
    
    # Verificar permisos
    try:
        user_membership = OrganizationMembership.objects.get(
            user=request.user, organization=organization, is_active=True
        )
        
        # Solo owner puede cambiar cualquier rol, admin puede cambiar roles menores
        if user_membership.role == 'owner' or (
            user_membership.role == 'admin' and target_membership.role not in ['owner', 'admin']
        ):
            data = json.loads(request.body)
            new_role = data.get('role')
            
            if new_role in ['admin', 'editor', 'viewer']:
                with transaction.atomic():
                    old_role = target_membership.role
                    target_membership.role = new_role
                    target_membership.save()
                    
                    # Log de actividad
                    log_activity(
                        user=request.user,
                        action='role_changed',
                        description=f'Rol de {target_membership.user.username} cambiado de {old_role} a {new_role}',
                        organization=organization,
                        request=request
                    )
                
                return JsonResponse({'success': True})
        
        return JsonResponse({'success': False, 'error': 'Sin permisos'})
        
    except OrganizationMembership.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Sin acceso'})


@login_required
@require_http_methods(["POST"])
def remove_member(request, org_slug, membership_id):
    """Remover miembro de la organización"""
    organization = get_object_or_404(Organization, slug=org_slug, is_active=True)
    target_membership = get_object_or_404(OrganizationMembership, id=membership_id, organization=organization)
    
    # Verificar permisos
    try:
        user_membership = OrganizationMembership.objects.get(
            user=request.user, organization=organization, is_active=True
        )
        
        # No se puede remover al owner, solo owner puede remover admin
        if target_membership.role == 'owner':
            return JsonResponse({'success': False, 'error': 'No se puede remover al propietario'})
        
        if user_membership.role == 'owner' or (
            user_membership.role == 'admin' and target_membership.role not in ['owner', 'admin']
        ):
            username = target_membership.user.username
            target_membership.is_active = False
            target_membership.save()
            
            # Log de actividad
            log_activity(
                user=request.user,
                action='user_removed',
                description=f'Usuario {username} removido de la organización',
                organization=organization,
                request=request
            )
            
            return JsonResponse({'success': True})
        
        return JsonResponse({'success': False, 'error': 'Sin permisos'})
        
    except OrganizationMembership.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Sin acceso'})


@login_required
@require_http_methods(["POST"])
def clear_old_logs(request, org_slug):
    """Limpiar logs antiguos (más de 90 días)"""
    organization = get_object_or_404(Organization, slug=org_slug, is_active=True)
    
    # Verificar permisos
    try:
        membership = OrganizationMembership.objects.get(
            user=request.user, organization=organization, is_active=True
        )
        if membership.role not in ['owner', 'admin']:
            return JsonResponse({'success': False, 'error': 'Sin permisos'})
    except OrganizationMembership.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Sin acceso'})
    
    from datetime import datetime, timedelta
    cutoff_date = datetime.now() - timedelta(days=90)
    
    deleted_count, _ = organization.activity_logs.filter(
        created_at__lt=cutoff_date
    ).delete()
    
    # Log de actividad
    log_activity(
        user=request.user,
        action='logs_cleared',
        description=f'Se eliminaron {deleted_count} logs antiguos',
        organization=organization,
        request=request
    )
    
    return JsonResponse({'success': True, 'deleted_count': deleted_count})


@login_required
def form_templates(request, org_slug):
    """Ver plantillas de formularios disponibles"""
    organization = get_object_or_404(Organization, slug=org_slug, is_active=True)
    
    # Verificar permisos
    try:
        membership = OrganizationMembership.objects.get(
            user=request.user, organization=organization, is_active=True
        )
        if not membership.can_edit_forms():
            messages.error(request, 'No tienes permisos para crear formularios.')
            return redirect('mainapp:dashboard', org_slug=org_slug)
    except OrganizationMembership.DoesNotExist:
        messages.error(request, 'No tienes acceso a esta organización.')
        return redirect('mainapp:select_organization')
    
    # Manejar petición de preview
    if request.GET.get('preview'):
        template_id = request.GET.get('preview')
        try:
            template = FormTemplate.objects.get(id=template_id, is_active=True)
            template_data = template.template_data  # Already a Python dict, no need to parse JSON
            
            # Procesar los campos para mostrar
            fields_data = []
            for field in template_data.get('fields', []):
                fields_data.append({
                    'label': field.get('label', ''),
                    'field_type': field.get('field_type', ''),
                    'is_required': field.get('is_required', False)
                })
            
            # Procesar lógica de negocio para hacerla más amigable
            business_logic_description = None
            if template.business_logic:
                # Crear una descripción más amigable basada en el tipo de plantilla
                if template.category == 'sales':
                    business_logic_description = {
                        'title': 'Automización de Ventas',
                        'features': [
                            'Calcula automáticamente el total de la venta',
                            'Determina el margen de ganancia por producto',
                            'Verifica disponibilidad en inventario',
                            'Actualiza stock automáticamente',
                            'Genera reportes de rentabilidad'
                        ]
                    }
                elif template.category == 'inventory':
                    business_logic_description = {
                        'title': 'Gestión de Inventario',
                        'features': [
                            'Rastrea movimientos de stock en tiempo real',
                            'Calcula valores de inventario',
                            'Genera alertas de stock bajo',
                            'Controla entradas y salidas',
                            'Mantiene histórico de transacciones'
                        ]
                    }
                elif template.category == 'hr':
                    business_logic_description = {
                        'title': 'Recursos Humanos',
                        'features': [
                            'Valida información de empleados',
                            'Calcula beneficios automáticamente',
                            'Genera expedientes digitales',
                            'Controla accesos y permisos',
                            'Procesa evaluaciones de desempeño'
                        ]
                    }
                elif template.category == 'customer':
                    business_logic_description = {
                        'title': 'Atención al Cliente',
                        'features': [
                            'Categoriza tickets automáticamente',
                            'Asigna prioridades por urgencia',
                            'Envía notificaciones automáticas',
                            'Rastrea tiempos de respuesta',
                            'Genera métricas de satisfacción'
                        ]
                    }
                elif template.category == 'finance':
                    business_logic_description = {
                        'title': 'Gestión Financiera',
                        'features': [
                            'Calcula totales y subtotales automáticamente',
                            'Genera reportes contables',
                            'Controla presupuestos y gastos',
                            'Valida transacciones financieras',
                            'Mantiene histórico de movimientos'
                        ]
                    }
                else:
                    business_logic_description = {
                        'title': 'Automatización Personalizada',
                        'features': [
                            'Procesa datos automáticamente',
                            'Valida información ingresada',
                            'Genera reportes dinámicos',
                            'Integra con otros sistemas',
                            'Mantiene auditoría completa'
                        ]
                    }
            
            preview_data = {
                'fields': fields_data,
                'business_logic': business_logic_description
            }
            
            return JsonResponse(preview_data)
        except FormTemplate.DoesNotExist:
            return JsonResponse({'error': 'Plantilla no encontrada'}, status=404)
        except Exception as e:
            return JsonResponse({'error': f'Error al procesar la plantilla: {str(e)}'}, status=500)
    
    templates = FormTemplate.objects.filter(is_active=True).order_by('category', 'name')
    categories = FormTemplate.CATEGORY_CHOICES
    
    context = {
        'organization': organization,
        'membership': membership,
        'templates': templates,
        'categories': categories,
    }
    return render(request, 'mainapp/form_templates.html', context)


@login_required
def create_form_from_template(request, org_slug, template_id):
    """Crear un formulario basado en una plantilla"""
    organization = get_object_or_404(Organization, slug=org_slug, is_active=True)
    template = get_object_or_404(FormTemplate, id=template_id, is_active=True)
    
    # Verificar permisos
    try:
        membership = OrganizationMembership.objects.get(
            user=request.user, organization=organization, is_active=True
        )
        if not membership.can_edit_forms():
            messages.error(request, 'No tienes permisos para crear formularios.')
            return redirect('mainapp:dashboard', org_slug=org_slug)
    except OrganizationMembership.DoesNotExist:
        messages.error(request, 'No tienes acceso a esta organización.')
        return redirect('mainapp:select_organization')
    
    if request.method == 'POST':
        with transaction.atomic():
            # Crear formulario basado en la plantilla
            template_data = template.template_data
            
            # Crear el formulario
            form = DynamicForm.objects.create(
                organization=organization,
                creator=request.user,
                title=template_data.get('title', template.name),
                description=template.description,
                is_public=template_data.get('is_public', False)
            )
            
            # Crear campos
            total_cost = 0
            for i, field_data in enumerate(template_data.get('fields', [])):
                # Buscar tipo de campo
                try:
                    field_type = FieldType.objects.get(name=field_data['field_type'])
                    
                    # Verificar si el usuario tiene suficientes monedas
                    if request.user.monedas < field_type.cost:
                        messages.error(request, f'No tienes suficientes monedas para agregar el campo "{field_data["label"]}"')
                        continue
                    
                    # Crear campo
                    DynamicFormField.objects.create(
                        form=form,
                        field_type=field_type,
                        label=field_data['label'],
                        help_text=field_data.get('help_text', ''),
                        is_required=field_data.get('is_required', False),
                        choices=field_data.get('choices', ''),
                        order=i
                    )
                    
                    # Descontar monedas
                    request.user.monedas -= field_type.cost
                    total_cost += field_type.cost
                    
                    # Registrar transacción
                    CoinTransaction.objects.create(
                        user=request.user,
                        organization=organization,
                        transaction_type='spend',
                        amount=field_type.cost,
                        description=f'Campo agregado: {field_data["label"]} ({field_type.display_name})',
                        related_form=form
                    )
                    
                except FieldType.DoesNotExist:
                    messages.warning(request, f'Tipo de campo "{field_data["field_type"]}" no encontrado')
                    continue
            
            # Actualizar costo total y guardar usuario
            form.total_cost = total_cost
            form.save()
            request.user.save()
            
            # Crear lógica de negocio si está definida
            if template.business_logic:
                BusinessLogicProcessor.objects.create(
                    form=form,
                    logic_type=template.category,
                    python_code=template.business_logic,
                    config_data={'template_id': template.id}
                )
            
            # Incrementar contador de uso de plantilla
            template.usage_count += 1
            template.save()
            
            # Log de actividad
            log_activity(
                user=request.user,
                action='create_form',
                description=f'Formulario creado desde plantilla: {template.name}',
                organization=organization,
                form=form,
                request=request
            )
            
            messages.success(request, f'¡Formulario "{form.title}" creado exitosamente desde la plantilla!')
            return redirect('mainapp:edit_form', org_slug=org_slug, form_id=form.id)
    
    context = {
        'organization': organization,
        'membership': membership,
        'template': template,
    }
    return render(request, 'mainapp/create_form_from_template.html', context)


@login_required
def inventory_dashboard(request, org_slug):
    """Dashboard de inventario para la organización"""
    organization = get_object_or_404(Organization, slug=org_slug, is_active=True)
    
    # Verificar permisos
    try:
        membership = OrganizationMembership.objects.get(
            user=request.user, organization=organization, is_active=True
        )
    except OrganizationMembership.DoesNotExist:
        messages.error(request, 'No tienes acceso a esta organización.')
        return redirect('mainapp:select_organization')
    
    # Estadísticas de inventario
    items = InventoryItem.objects.filter(organization=organization, is_active=True)
    transactions = InventoryTransaction.objects.filter(organization=organization)
    
    stats = {
        'total_items': items.count(),
        'low_stock_items': items.filter(current_stock__lte=models.F('min_stock')).count(),
        'total_transactions': transactions.count(),
        'total_value': sum(item.current_stock * item.purchase_price for item in items),
    }
    
    # Artículos con stock bajo
    low_stock_items = items.filter(current_stock__lte=models.F('min_stock'))[:5]
    
    # Transacciones recientes
    recent_transactions = transactions.order_by('-created_at')[:10]
    
    context = {
        'organization': organization,
        'membership': membership,
        'stats': stats,
        'low_stock_items': low_stock_items,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'mainapp/inventory_dashboard.html', context)


@login_required
def inventory_items(request, org_slug):
    """Listado de artículos de inventario"""
    organization = get_object_or_404(Organization, slug=org_slug, is_active=True)
    
    # Verificar permisos
    try:
        membership = OrganizationMembership.objects.get(
            user=request.user, organization=organization, is_active=True
        )
    except OrganizationMembership.DoesNotExist:
        messages.error(request, 'No tienes acceso a esta organización.')
        return redirect('mainapp:select_organization')
    
    items = InventoryItem.objects.filter(organization=organization, is_active=True).order_by('name')
    
    context = {
        'organization': organization,
        'membership': membership,
        'items': items,
    }
    return render(request, 'mainapp/inventory_items.html', context)


@login_required
def inventory_transactions(request, org_slug):
    """Historial de transacciones de inventario"""
    organization = get_object_or_404(Organization, slug=org_slug, is_active=True)
    
    # Verificar permisos
    try:
        membership = OrganizationMembership.objects.get(
            user=request.user, organization=organization, is_active=True
        )
    except OrganizationMembership.DoesNotExist:
        messages.error(request, 'No tienes acceso a esta organización.')
        return redirect('mainapp:select_organization')
    
    transactions = InventoryTransaction.objects.filter(
        organization=organization
    ).order_by('-created_at')
    
    context = {
        'organization': organization,
        'membership': membership,
        'transactions': transactions,
    }
    return render(request, 'mainapp/inventory_transactions.html', context)
