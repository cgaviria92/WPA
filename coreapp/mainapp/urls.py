from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('forms/create/', views.create_form, name='create_form'),
    path('forms/<int:form_id>/edit/', views.edit_form, name='edit_form'),
    path('forms/<int:form_id>/view/', views.view_form, name='view_form'),
    path('forms/<int:form_id>/submissions/', views.form_submissions, name='form_submissions'),
    path('forms/<int:form_id>/add-field/', views.add_field_to_form, name='add_field_to_form'),
    path('fields/<int:field_id>/delete/', views.delete_field, name='delete_field'),
    path('form-success/', views.form_success, name='form_success'),
]
