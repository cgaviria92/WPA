#!/usr/bin/env python3

# Script para corregir tipos de campo en setup_form_templates.py

import sys
import os

# Cambiar al directorio correcto
os.chdir(r'C:\Users\ingca\OneDrive\Desktop\personal\wpa\coreapp')

file_path = 'mainapp/management/commands/setup_form_templates.py'

try:
    # Leer el archivo
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Contar ocurrencias antes
    before_text_short = content.count("'field_type': 'text_short'")
    before_text_long = content.count("'field_type': 'text_long'")
    before_selection = content.count("'field_type': 'selection'")
    
    print(f"Antes: text_short={before_text_short}, text_long={before_text_long}, selection={before_selection}")
    
    # Hacer los reemplazos
    content = content.replace("'field_type': 'text_short'", "'field_type': 'text'")
    content = content.replace("'field_type': 'text_long'", "'field_type': 'textarea'")
    content = content.replace("'field_type': 'selection'", "'field_type': 'choice'")
    
    # Contar ocurrencias después
    after_text = content.count("'field_type': 'text'")
    after_textarea = content.count("'field_type': 'textarea'")
    after_choice = content.count("'field_type': 'choice'")
    
    print(f"Después: text={after_text}, textarea={after_textarea}, choice={after_choice}")
    
    # Escribir el archivo actualizado
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('✅ Archivo actualizado exitosamente')
    
except Exception as e:
    print(f'❌ Error: {e}')
