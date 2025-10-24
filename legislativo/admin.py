
from django.contrib import admin
from .models import Projeto, Voto, Cargo, VereadorProfile

admin.site.register(VereadorProfile)
admin.site.register(Cargo)

admin.site.register(Projeto)
admin.site.register(Voto)