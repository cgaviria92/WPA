from django import template

register = template.Library()

@register.filter
def lookup(dictionary, key):
    """Permite acceder a elementos de un diccionario en templates"""
    if dictionary and isinstance(dictionary, dict):
        return dictionary.get(key, '')
    return ''
