from django.contrib import admin
from .models import (
    CustomUser, Organization, OrganizationMembership, FieldType, 
    DynamicForm, DynamicFormField, FormSubmission, CoinTransaction, ActivityLog
)

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'monedas', 'created_at']
    list_filter = ['is_staff', 'created_at']
    search_fields = ['username', 'email']
    readonly_fields = ['created_at']

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'owner__username']
    readonly_fields = ['created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(OrganizationMembership)
class OrganizationMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'role', 'is_active', 'joined_at']
    list_filter = ['role', 'is_active', 'joined_at']
    search_fields = ['user__username', 'organization__name']

@admin.register(FieldType)
class FieldTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'cost', 'storage_multiplier']
    list_editable = ['cost', 'storage_multiplier']

@admin.register(DynamicForm)
class DynamicFormAdmin(admin.ModelAdmin):
    list_display = ['title', 'organization', 'creator', 'total_cost', 'is_active', 'is_public', 'created_at']
    list_filter = ['is_active', 'is_public', 'created_at', 'organization']
    search_fields = ['title', 'description', 'organization__name']
    readonly_fields = ['total_cost', 'created_at', 'updated_at']

@admin.register(DynamicFormField)
class DynamicFormFieldAdmin(admin.ModelAdmin):
    list_display = ['label', 'form', 'field_type', 'is_required', 'order']
    list_filter = ['field_type', 'is_required', 'form__organization']
    search_fields = ['label', 'form__title']
    list_editable = ['order']

@admin.register(FormSubmission)
class FormSubmissionAdmin(admin.ModelAdmin):
    list_display = ['form', 'submitted_by', 'submitted_at', 'ip_address']
    list_filter = ['submitted_at', 'form__organization']
    readonly_fields = ['submitted_at', 'data', 'ip_address']

@admin.register(CoinTransaction)
class CoinTransactionAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'transaction_type', 'amount', 'description', 'created_at']
    list_filter = ['transaction_type', 'created_at', 'organization']
    readonly_fields = ['created_at']

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'organization', 'action', 'description', 'created_at']
    list_filter = ['action', 'created_at', 'organization']
    readonly_fields = ['created_at']
    search_fields = ['user__username', 'description']
