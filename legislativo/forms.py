# legislativo/forms.py
from django import forms
from .models import Projeto

class ProjetoForm(forms.ModelForm):
    class Meta:
        model = Projeto
        # A Secretaria só precisa cadastrar estes campos. 
        # O 'status' inicial será sempre 'PREPARACAO' (definido no Model).
        # O 'abertura_voto' será definido pelo Gerente.
        fields = ['titulo', 'tipo', 'descricao', 'quorum_minimo', 'tempo_limite_segundos']
        
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 4}),
        }