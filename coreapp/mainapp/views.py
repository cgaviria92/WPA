from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import CustomUser, FieldType, DynamicForm, DynamicFormField, FormSubmission, CoinTransaction
from .forms import DynamicFormCreationForm, DynamicFormFieldForm, UserRegistrationForm
import json

def index(request):
    """Página principal"""
    forms = DynamicForm.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'mainapp/index.html', {'forms': forms})

def register(request):
    """Registro de usuarios"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            if user.is_admin_user:
                messages.success(request, '¡Felicidades! Eres el primer usuario y ahora eres administrador con 1000 monedas.')
            else:
                messages.success(request, 'Registro exitoso. Bienvenido al sistema.')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request):
    """Panel de control del usuario"""
    user_forms = DynamicForm.objects.filter(creator=request.user).order_by('-created_at')
    recent_transactions = CoinTransaction.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    context = {
        'user_forms': user_forms,
        'recent_transactions': recent_transactions,
        'available_field_types': FieldType.objects.all(),
    }
    return render(request, 'mainapp/dashboard.html', context)

@login_required
def create_form(request):
    """Crear nuevo formulario dinámico"""
    if request.method == 'POST':
        form = DynamicFormCreationForm(request.POST)
        if form.is_valid():
            dynamic_form = form.save(commit=False)
            dynamic_form.creator = request.user
            dynamic_form.save()
            messages.success(request, 'Formulario creado exitosamente.')
            return redirect('edit_form', form_id=dynamic_form.id)
    else:
        form = DynamicFormCreationForm()
    
    return render(request, 'mainapp/create_form.html', {'form': form})

@login_required
def edit_form(request, form_id):
    """Editar formulario dinámico"""
    dynamic_form = get_object_or_404(DynamicForm, id=form_id, creator=request.user)
    fields = dynamic_form.fields.all().order_by('order')
    field_types = FieldType.objects.all()
    
    # Si no hay tipos de campo, mostrar mensaje de error
    if not field_types.exists():
        messages.error(request, 
            'No hay tipos de campo disponibles. Contacta al administrador para configurar el sistema.')
    
    context = {
        'dynamic_form': dynamic_form,
        'fields': fields,
        'field_types': field_types,
        'has_field_types': field_types.exists(),
    }
    return render(request, 'mainapp/edit_form.html', context)

@login_required
@csrf_exempt
@require_http_methods(["POST"])
def add_field_to_form(request, form_id):
    """Agregar campo a formulario (AJAX)"""
    dynamic_form = get_object_or_404(DynamicForm, id=form_id, creator=request.user)
    
    try:
        data = json.loads(request.body)
        field_type_id = data.get('field_type_id')
        label = data.get('label')
        is_required = data.get('is_required', False)
        help_text = data.get('help_text', '')
        choices = data.get('choices', '')
        
        field_type = get_object_or_404(FieldType, id=field_type_id)
        
        # Verificar si el usuario puede costear el campo
        if not request.user.can_afford(field_type.cost):
            return JsonResponse({
                'success': False,
                'error': f'No tienes suficientes monedas. Necesitas {field_type.cost} monedas.'
            })
        
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
        request.user.spend_coins(field_type.cost)
        
        # Registrar la transacción
        CoinTransaction.objects.create(
            user=request.user,
            transaction_type='spend',
            amount=field_type.cost,
            description=f'Campo agregado: {label} ({field_type.display_name})',
            related_form=dynamic_form
        )
        
        # Actualizar costo total del formulario
        dynamic_form.total_cost = dynamic_form.calculate_total_cost()
        dynamic_form.save()
        
        return JsonResponse({
            'success': True,
            'field_id': field.id,
            'remaining_coins': request.user.monedas
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def delete_field(request, field_id):
    """Eliminar campo de formulario"""
    field = get_object_or_404(DynamicFormField, id=field_id, form__creator=request.user)
    form_id = field.form.id
    
    # Reembolsar monedas (opcional - puedes quitar esto si no quieres reembolsos)
    refund_amount = field.field_type.cost // 2  # Reembolso del 50%
    request.user.monedas += refund_amount
    request.user.save()
    
    # Registrar transacción de reembolso
    CoinTransaction.objects.create(
        user=request.user,
        transaction_type='earn',
        amount=refund_amount,
        description=f'Reembolso por eliminar campo: {field.label}',
        related_form=field.form
    )
    
    field.delete()
    
    # Actualizar costo total del formulario
    dynamic_form = field.form
    dynamic_form.total_cost = dynamic_form.calculate_total_cost()
    dynamic_form.save()
    
    messages.success(request, f'Campo eliminado. Reembolso: {refund_amount} monedas.')
    return redirect('edit_form', form_id=form_id)

def view_form(request, form_id):
    """Ver y enviar datos a un formulario público"""
    dynamic_form = get_object_or_404(DynamicForm, id=form_id, is_active=True)
    fields = dynamic_form.fields.all().order_by('order')
    
    if request.method == 'POST':
        submission_data = {}
        valid = True
        errors = {}
        
        for field in fields:
            field_name = f'field_{field.id}'
            value = request.POST.get(field_name)
            
            if field.is_required and not value:
                valid = False
                errors[field_name] = 'Este campo es obligatorio'
            else:
                submission_data[field_name] = value
        
        if valid:
            # Guardar envío
            FormSubmission.objects.create(
                form=dynamic_form,
                submitted_by=request.user if request.user.is_authenticated else None,
                data=submission_data
            )
            messages.success(request, 'Formulario enviado exitosamente.')
            return redirect('form_success')
    
    context = {
        'dynamic_form': dynamic_form,
        'fields': fields,
    }
    return render(request, 'mainapp/view_form.html', context)

def form_success(request):
    """Página de éxito después de enviar un formulario"""
    return render(request, 'mainapp/form_success.html')

@login_required
def form_submissions(request, form_id):
    """Ver envíos de un formulario (solo el creador)"""
    dynamic_form = get_object_or_404(DynamicForm, id=form_id, creator=request.user)
    submissions = dynamic_form.submissions.all().order_by('-submitted_at')
    fields = dynamic_form.fields.all().order_by('order')
    
    context = {
        'dynamic_form': dynamic_form,
        'submissions': submissions,
        'fields': fields,
    }
    return render(request, 'mainapp/form_submissions.html', context)
