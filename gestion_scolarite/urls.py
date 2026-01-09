from django.contrib import admin
from django.urls import path, include  # inclure include()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),  # redirige la racine vers les URLs de l'app core
]
