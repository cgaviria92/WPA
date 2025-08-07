from django.urls import path
from . import views

app_name = 'mainapp'

urlpatterns = [
    # Páginas públicas
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('form-success/', views.form_success, name='form_success'),
    
    # Gestión de organizaciones
    path('organizations/', views.select_organization, name='select_organization'),
    path('organizations/create/', views.create_organization, name='create_organization'),
    
    # URLs específicas por organización
    path('org/<slug:org_slug>/', views.dashboard, name='dashboard'),
    path('org/<slug:org_slug>/forms/create/', views.create_form, name='create_form'),
    path('org/<slug:org_slug>/forms/create/from-template/<int:template_id>/', views.create_form_from_template, name='create_form_from_template'),
    path('org/<slug:org_slug>/forms/templates/', views.form_templates, name='form_templates'),
    path('org/<slug:org_slug>/forms/<int:form_id>/edit/', views.edit_form, name='edit_form'),
    path('org/<slug:org_slug>/forms/<int:form_id>/view/', views.view_form, name='view_form'),
    path('org/<slug:org_slug>/forms/<int:form_id>/submissions/', views.form_submissions, name='form_submissions'),
    path('org/<slug:org_slug>/forms/<int:form_id>/add-field/', views.add_field_to_form, name='add_field_to_form'),
    path('org/<slug:org_slug>/fields/<int:field_id>/delete/', views.delete_field, name='delete_field'),
    
    # Inventario y lógica de negocio
    path('org/<slug:org_slug>/inventory/', views.inventory_dashboard, name='inventory_dashboard'),
    path('org/<slug:org_slug>/inventory/items/', views.inventory_items, name='inventory_items'),
    path('org/<slug:org_slug>/inventory/transactions/', views.inventory_transactions, name='inventory_transactions'),
    
    # Gestión de equipo y logs
    path('org/<slug:org_slug>/team/', views.team_management, name='team_management'),
    path('org/<slug:org_slug>/team/invite/', views.invite_user, name='invite_user'),
    path('org/<slug:org_slug>/team/bulk-invite/', views.bulk_invite_users, name='bulk_invite_users'),
    path('org/<slug:org_slug>/team/member/<int:membership_id>/role/', views.change_member_role, name='change_member_role'),
    path('org/<slug:org_slug>/team/member/<int:membership_id>/remove/', views.remove_member, name='remove_member'),
    path('org/<slug:org_slug>/logs/', views.activity_logs, name='activity_logs'),
    path('org/<slug:org_slug>/logs/clear/', views.clear_old_logs, name='clear_old_logs'),
]
