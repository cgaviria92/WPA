from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, DynamicForm, DynamicFormField, FieldType, Organization

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mejorar estilos de los campos
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class OrganizationCreationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'description', 'logo']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nombre de tu organización/empresa'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Describe tu organización (opcional)'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }

class DynamicFormCreationForm(forms.ModelForm):
    class Meta:
        model = DynamicForm
        fields = ['title', 'description', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Título del formulario'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Descripción opcional'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'is_public': 'Permitir acceso público',
        }
        help_texts = {
            'is_public': 'Si está marcado, cualquier persona con el enlace puede llenar este formulario (no requiere registro).',
        }

class DynamicFormFieldForm(forms.ModelForm):
    class Meta:
        model = DynamicFormField
        fields = [
            'field_type', 'label', 'help_text', 'is_required', 'choices', 
            'max_length', 'min_value', 'max_value',
            'max_file_size_mb', 'allowed_file_types', 'file_cost_per_mb'
        ]
        widgets = {
            'field_type': forms.Select(attrs={'class': 'form-control'}),
            'label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Etiqueta del campo'}),
            'help_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Texto de ayuda (opcional)'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'choices': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Una opción por línea'}),
            'max_length': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_file_size_mb': forms.NumberInput(attrs={
                'class': 'form-control', 
                'step': '0.1',
                'placeholder': '5.0'
            }),
            'allowed_file_types': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'image/*,application/pdf,.doc,.docx,.txt'
            }),
            'file_cost_per_mb': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.1',
                'placeholder': '1.0'
            }),
        }
        labels = {
            'max_file_size_mb': 'Tamaño máximo (MB)',
            'allowed_file_types': 'Tipos de archivo permitidos',
            'file_cost_per_mb': 'Costo por MB (monedas)',
        }
        help_texts = {
            'max_file_size_mb': 'Tamaño máximo del archivo en megabytes',
            'allowed_file_types': 'Tipos MIME o extensiones separados por comas (ej: image/*,application/pdf,.txt)',
            'file_cost_per_mb': 'Monedas que se cobrarán por cada MB subido',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostrar el costo de cada tipo de campo
        field_type_choices = []
        for field_type in FieldType.objects.all():
            field_type_choices.append((field_type.id, f"{field_type.display_name} ({field_type.cost} monedas)"))
        self.fields['field_type'].choices = field_type_choices

class UserInvitationForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@ejemplo.com'
        }),
        label='Email del usuario'
    )
    role = forms.ChoiceField(
        choices=[
            ('admin', 'Administrador'),
            ('editor', 'Editor'),
            ('viewer', 'Visualizador'),
            ('form_filler', 'Llenador de Formularios'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Rol'
    )
    
    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            user = CustomUser.objects.get(email=email)
            return email
        except CustomUser.DoesNotExist:
            raise forms.ValidationError('No existe un usuario con este email. El usuario debe registrarse primero.')

class BulkUserInviteForm(forms.Form):
    emails = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'email1@ejemplo.com\nemail2@ejemplo.com\nemail3@ejemplo.com'
        }),
        label='Emails (uno por línea)',
        help_text='Ingresa un email por línea'
    )
    role = forms.ChoiceField(
        choices=[
            ('admin', 'Administrador'),
            ('editor', 'Editor'),
            ('viewer', 'Visualizador'),
            ('form_filler', 'Llenador de Formularios'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Rol para todos los usuarios'
    )
    
    def clean_emails(self):
        emails_text = self.cleaned_data['emails']
        emails = [email.strip() for email in emails_text.split('\n') if email.strip()]
        
        if not emails:
            raise forms.ValidationError('Debes ingresar al menos un email.')
        
        # Validar que todos sean emails válidos
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError
        
        valid_emails = []
        for email in emails:
            try:
                validate_email(email)
                valid_emails.append(email)
            except ValidationError:
                raise forms.ValidationError(f'Email inválido: {email}')
        
        return valid_emails


class BulkUserInviteForm(forms.Form):
    users_data = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'email1@example.com,editor\nemail2@example.com,viewer\nemail3@example.com,admin'
        }),
        label='Datos de Usuarios',
        help_text='Formato: email,rol (uno por línea o separados por ;). Roles válidos: admin, editor, viewer'
    )
    
    def clean_users_data(self):
        data = self.cleaned_data['users_data']
        
        if not data.strip():
            raise forms.ValidationError('Debes ingresar datos de usuarios.')
        
        # Validar formato
        lines = [line.strip() for line in data.replace(';', '\n').split('\n') if line.strip()]
        
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        valid_roles = ['admin', 'editor', 'viewer']
        
        for line in lines:
            parts = line.split(',')
            if len(parts) != 2:
                raise forms.ValidationError(f'Formato inválido en línea: {line}. Usa: email,rol')
            
            email, role = parts[0].strip(), parts[1].strip()
            
            try:
                validate_email(email)
            except DjangoValidationError:
                raise forms.ValidationError(f'Email inválido: {email}')
            
            if role not in valid_roles:
                raise forms.ValidationError(f'Rol inválido: {role}. Usa: {", ".join(valid_roles)}')
        
        return data


class CustomFileField(forms.FileField):
    """Campo de archivo personalizado con validaciones de tamaño y tipo"""
    
    def __init__(self, form_field, *args, **kwargs):
        self.form_field = form_field
        super().__init__(*args, **kwargs)
        
        # Configurar validaciones basadas en el campo del formulario
        if form_field.max_file_size_mb:
            self.max_size = form_field.get_max_file_size_bytes()
        
        if form_field.allowed_file_types:
            self.allowed_types = form_field.get_allowed_file_types_list()
    
    def validate(self, value):
        super().validate(value)
        
        if value is None:
            return
        
        # Validar tamaño
        if hasattr(self, 'max_size') and value.size > self.max_size:
            max_mb = self.max_size / (1024 * 1024)
            current_mb = value.size / (1024 * 1024)
            raise forms.ValidationError(
                f'El archivo es demasiado grande ({current_mb:.1f} MB). '
                f'El tamaño máximo permitido es {max_mb:.1f} MB.'
            )
        
        # Validar tipo de archivo
        if hasattr(self, 'allowed_types'):
            import mimetypes
            file_type = mimetypes.guess_type(value.name)[0] or ''
            file_ext = '.' + value.name.split('.')[-1].lower() if '.' in value.name else ''
            
            type_allowed = False
            for allowed in self.allowed_types:
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
                allowed_display = ', '.join(self.allowed_types)
                raise forms.ValidationError(
                    f'Tipo de archivo no permitido. Tipos permitidos: {allowed_display}'
                )


class FileUploadForm(forms.Form):
    """Formulario dinámico para subir archivos"""
    
    def __init__(self, form_fields, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field in form_fields:
            if field.field_type.name == 'file':
                self.fields[f'field_{field.id}'] = CustomFileField(
                    form_field=field,
                    required=field.is_required,
                    help_text=field.help_text
                )
