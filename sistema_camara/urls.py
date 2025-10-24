# sistema_camara/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # URLs de autenticação do Django (login, logout, etc.)
    path('contas/', include('django.contrib.auth.urls')), 
    # URLs do nosso app
    path('', include('legislativo.urls')), 
]