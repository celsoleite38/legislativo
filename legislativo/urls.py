# legislativo/urls.py
from django.urls import path
from . import views

app_name = 'legislativo'

urlpatterns = [
    # Tela Pública (Placar)
    path('', views.tela_principal, name='tela_principal'), 
    
    
    path('painel/', views.painel_vereador, name='painel_vereador'),
    path('secretaria/', views.painel_secretaria, name='painel_secretaria'),
    path('gerente/', views.painel_gerente, name='painel_gerente'), 
    path('votar/<int:projeto_id>/', views.votar, name='votar'),
    
    
    path('iniciar_votacao/<int:projeto_id>/', views.iniciar_votacao, name='iniciar_votacao'),
    path('encerrar_votacao/<int:projeto_id>/', views.encerrar_votacao, name='encerrar_votacao'),
    
    path('api/resultados/<int:projeto_id>/', views.resultados_api, name='resultados_api'),
]