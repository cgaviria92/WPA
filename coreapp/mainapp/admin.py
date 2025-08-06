from django.contrib import admin
from .models import CustomUser, FieldType, DynamicForm, DynamicFormField, FormSubmission, CoinTransaction

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'monedas', 'is_admin_user', 'created_at']
    list_filter = ['is_admin_user', 'is_staff', 'created_at']
    search_fields = ['username', 'email']
    readonly_fields = ['created_at']

@admin.register(FieldType)
class FieldTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'cost', 'storage_multiplier']
    list_editable = ['cost', 'storage_multiplier']

@admin.register(DynamicForm)
class DynamicFormAdmin(admin.ModelAdmin):
    list_display = ['title', 'creator', 'total_cost', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'creator']
    search_fields = ['title', 'description']
    readonly_fields = ['total_cost', 'created_at', 'updated_at']

@admin.register(DynamicFormField)
class DynamicFormFieldAdmin(admin.ModelAdmin):
    list_display = ['label', 'form', 'field_type', 'is_required', 'order']
    list_filter = ['field_type', 'is_required']
    search_fields = ['label', 'form__title']
    list_editable = ['order']

@admin.register(FormSubmission)
class FormSubmissionAdmin(admin.ModelAdmin):
    list_display = ['form', 'submitted_by', 'submitted_at']
    list_filter = ['submitted_at', 'form']
    readonly_fields = ['submitted_at', 'data']

@admin.register(CoinTransaction)
class CoinTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'transaction_type', 'amount', 'description', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    readonly_fields = ['created_at']
