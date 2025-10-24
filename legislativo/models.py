# legislativo/models.py
from django.db import models
from django.contrib.auth.models import User

# Adicionar ao topo junto com os imports existentes


class Cargo(models.Model):
    # Usado para identificar os cargos que têm peso (Presidente, Vice, etc.)
    nome = models.CharField(max_length=50, unique=True)
    peso_voto = models.IntegerField(default=1) # 1 para voto normal, 0 para Presidente (voto de Minerva)

    class Meta:
        verbose_name = "Cargo na Mesa Diretora"
        verbose_name_plural = "Cargos na Mesa Diretora"

    def __str__(self):
        return self.nome


class VereadorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    
    # Informações Legislativas
    nome_completo = models.CharField(max_length=255)
    apelido_parlamentar = models.CharField(max_length=100, blank=True, null=True)
    
    # Cargo na Mesa Diretora (Opcional)
    cargo_mesa = models.ForeignKey(
        Cargo, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Cargo na Mesa"
    )
    
    # Status
    ativo = models.BooleanField(default=True) # Indica se está em exercício
    
    class Meta:
        verbose_name = "Perfil do Vereador"
        verbose_name_plural = "Perfis dos Vereadores"

    def __str__(self):
        return self.nome_completo
        
    @property
    def is_presidente(self):
        return self.cargo_mesa and "Presidente" in self.cargo_mesa.nome


class Projeto(models.Model):
    # Tipos de Proposição
    TIPO_PROPOSICAO = (
        ('PL', 'Projeto de Lei Ordinária'),
        ('PLC', 'Projeto de Lei Complementar'),
        ('PEC', 'Proposta de Emenda à Lei Orgânica'),
        ('REQ', 'Requerimento'),
    )
    
    # Status de Votação
    STATUS_VOTACAO = (
        ('PREPARACAO', 'Em Preparação/Pauta'),
        ('ABERTO', 'Aberto para Votação'),
        ('FECHADO', 'Votação Encerrada'),
    )
    
    # Quórum Necessário
    QUORUM_NECESSARIO = (
        ('SIMPLES', 'Maioria Simples (PL, REQ)'),
        ('ABSOLUTA', 'Maioria Absoluta (PLC)'),
        ('DOIS_TERCOS', '2/3 dos Vereadores (PEC)'),
    )

    titulo = models.CharField(max_length=255)
    tipo = models.CharField(max_length=10, choices=TIPO_PROPOSICAO, default='PL')
    descricao = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_VOTACAO, default='PREPARACAO')
    quorum_minimo = models.CharField(max_length=20, choices=QUORUM_NECESSARIO, default='SIMPLES')
    
    # Controle de Tempo
    tempo_limite_segundos = models.IntegerField(default=60) # Padrão: 60 segundos
    abertura_voto = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Projeto de Lei"
        verbose_name_plural = "Projetos de Lei"

    def __str__(self):
        return f'{self.get_tipo_display()} N° {self.id}: {self.titulo}'
    
    def votos_sim(self):
        return self.voto_set.filter(escolha='SIM').count()
    
    def votos_nao(self):
        return self.voto_set.filter(escolha='NAO').count()
    
    def votos_abstencao(self):
        return self.voto_set.filter(escolha='ABSTER').count()

class Voto(models.Model):
    ESCOLHAS_VOTO = (
        ('SIM', 'Sim'),
        ('NAO', 'Não'),
        ('ABSTER', 'Abstenção'),
    )
    
    projeto = models.ForeignKey(Projeto, on_delete=models.CASCADE)
    vereador = models.ForeignKey(User, on_delete=models.CASCADE)
    escolha = models.CharField(max_length=10, choices=ESCOLHAS_VOTO)
    data_voto = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('projeto', 'vereador') 
        verbose_name = "Voto de Vereador"
        verbose_name_plural = "Votos de Vereadores"

    def __str__(self):
        return f'{self.vereador.username} votou em {self.projeto.titulo} ({self.escolha})'