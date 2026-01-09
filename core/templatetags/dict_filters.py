from django import template

register = template.Library()

@register.filter
def dict_get(d, key):
    if d:
        return d.get(key)
    return None
from django import template

register = template.Library()

@register.filter
def dict_get(d, key):
    return d.get(key)
