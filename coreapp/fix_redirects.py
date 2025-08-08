import re

with open('mainapp/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar todos los redirects sin namespace
patterns = [
    (r"redirect\('select_organization'\)", "redirect('mainapp:select_organization')"),
    (r"redirect\('dashboard'", "redirect('mainapp:dashboard'"),
    (r"redirect\('edit_form'", "redirect('mainapp:edit_form'"),
    (r"redirect\('index'\)", "redirect('mainapp:index')"),
    (r"redirect\('form_success'\)", "redirect('mainapp:form_success')"),
    (r"redirect\('team_management'", "redirect('mainapp:team_management'"),
]

for pattern, replacement in patterns:
    content = re.sub(pattern, replacement, content)

with open('mainapp/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Redirects actualizados en views.py')
