from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Permite acceder a elementos de un diccionario en templates"""
    print(f"LOOKUP DEBUG: dictionary={dictionary}, key='{key}', type={type(dictionary)}")
    if dictionary and isinstance(dictionary, dict):
        result = dictionary.get(key, '')
        print(f"LOOKUP RESULT: '{result}'")
        return result
    print(f"LOOKUP: No es diccionario o está vacío")
    return ''

@register.filter
def field_key(field_id):
    """Crea la clave para acceder a los datos del campo"""
    key = f"field_{field_id}"
    print(f"FIELD_KEY: field_id={field_id} -> key='{key}'")
    return key
