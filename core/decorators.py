from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect

def groupe_requis(nom_groupe):
    def check(user):
        return user.groups.filter(name=nom_groupe).exists() or user.is_superuser
    return user_passes_test(check, login_url='login')

from django.contrib.auth.decorators import user_passes_test

def groupe_requis(nom_groupe):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.groups.filter(name=nom_groupe).exists() or request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            else:
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("Accès interdit")
        return _wrapped_view
    return decorator
