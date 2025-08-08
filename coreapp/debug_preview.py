#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coreapp.settings')
django.setup()

from mainapp.models import FormTemplate, Organization, OrganizationMembership
from django.contrib.auth import get_user_model
from django.http import JsonResponse

User = get_user_model()

# Get test data
user = User.objects.first()
org = Organization.objects.first()
template = FormTemplate.objects.first()

print(f"User: {user.username}")
print(f"Organization: {org.slug}")
print(f"Template: {template.id} - {template.name}")

# Check membership
try:
    membership = OrganizationMembership.objects.get(user=user, organization=org, is_active=True)
    print(f"Membership found: {membership.role}")
    print(f"Can edit forms: {membership.can_edit_forms()}")
except OrganizationMembership.DoesNotExist:
    print("No membership found")

# Test the preview logic
try:
    template_data = template.template_data
    print(f"Template data type: {type(template_data)}")
    print(f"Template data keys: {list(template_data.keys())}")
    
    # Process fields like in the view
    fields_data = []
    for field in template_data.get('fields', []):
        fields_data.append({
            'label': field.get('label', ''),
            'field_type': field.get('field_type', ''),
            'is_required': field.get('is_required', False)
        })
    
    print(f"Processed {len(fields_data)} fields")
    for field in fields_data:
        print(f"  - {field['label']} ({field['field_type']}) {'*' if field['is_required'] else ''}")
    
    preview_data = {
        'fields': fields_data,
        'business_logic': template.business_logic if template.business_logic else None
    }
    
    print("Preview data created successfully!")
    print(f"Business logic: {preview_data['business_logic']}")
    
except Exception as e:
    print(f"Error processing template: {e}")
    import traceback
    traceback.print_exc()
