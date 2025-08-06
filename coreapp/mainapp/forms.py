from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, DynamicForm, DynamicFormField, FieldType

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user

class DynamicFormCreationForm(forms.ModelForm):
    class Meta:
        model = DynamicForm
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título del formulario'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descripción opcional'}),
        }

class DynamicFormFieldForm(forms.ModelForm):
    class Meta:
        model = DynamicFormField
        fields = ['field_type', 'label', 'help_text', 'is_required', 'choices', 'max_length', 'min_value', 'max_value']
        widgets = {
            'field_type': forms.Select(attrs={'class': 'form-control'}),
            'label': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Etiqueta del campo'}),
            'help_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Texto de ayuda (opcional)'}),
            'is_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'choices': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Una opción por línea'}),
            'max_length': forms.NumberInput(attrs={'class': 'form-control'}),
            'min_value': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_value': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Mostrar el costo de cada tipo de campo
        field_type_choices = []
        for field_type in FieldType.objects.all():
            field_type_choices.append((field_type.id, f"{field_type.display_name} ({field_type.cost} monedas)"))
        self.fields['field_type'].choices = field_type_choices
