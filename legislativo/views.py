# legislativo/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from .models import Projeto, Voto
from .forms import ProjetoForm

TOTAL_VEREADORES = User.objects.count()

def check_is_secretaria(user):
    return user.groups.filter(name='Secretaria Geral').exists()

def check_is_gerente(user):
    return user.groups.filter(name='Gerente de Votação').exists()


def tela_principal(request):
    # Pega o projeto que está ATIVO ou o último FECHADO
    projeto = Projeto.objects.filter(status__in=['ABERTO', 'FECHADO']).order_by('-abertura_voto').first()
    
    context = {
        'projeto_ativo': projeto,
        'total_vereadores': TOTAL_VEREADORES
    }
    return render(request, 'legislativo/tela_principal.html', context)


# --- 2. Painel do Vereador/Gerente ---
@login_required
def painel_vereador(request):
    
    # 1. Redirecionamento da Secretaria Geral
    if check_is_secretaria(request.user):
        return redirect('legislativo:painel_secretaria')
        
    # 2. Redirecionamento do Gerente de Votação
    if check_is_gerente(request.user):
        return redirect('legislativo:painel_gerente')
        
    # --- Lógica do Vereador Comum ---
    
    # Pega o projeto que está ABERTO para votação
    projeto_ativo = Projeto.objects.filter(status='ABERTO').order_by('-abertura_voto').first()

    # Inicializa voto_vereador para evitar o NameError se não houver projeto ativo
    voto_vereador = None 
    
    if projeto_ativo:
        # Busca o voto do usuário para o projeto ativo
        voto_vereador = Voto.objects.filter(
            projeto=projeto_ativo, 
            vereador=request.user
        ).first()

    # Busca projetos na pauta (embora um vereador comum não deva interagir com eles,
    # mantemos a variável para consistência se você quiser exibir algo.)
    projetos_na_pauta = Projeto.objects.filter(status='PREPARACAO').order_by('id')


    context = {
        'projeto_ativo': projeto_ativo,
        'voto_vereador': voto_vereador,
        'projetos_na_pauta': projetos_na_pauta, # Adicionada para que o template a use se necessário
    }
    return render(request, 'legislativo/painel_vereador.html', context)


@login_required
def painel_gerente(request):
    if not check_is_gerente(request.user):
        return HttpResponseForbidden("Acesso negado. Você não é Gerente de Votação.")
        
    projeto_ativo = Projeto.objects.filter(status='ABERTO').order_by('-abertura_voto').first()
    projetos_na_pauta = Projeto.objects.filter(status='PREPARACAO').order_by('id')
    projetos_encerrados = Projeto.objects.filter(status='FECHADO').order_by('-abertura_voto')[:5]

    context = {
        'projeto_ativo': projeto_ativo,
        'projetos_na_pauta': projetos_na_pauta,
        'projetos_encerrados': projetos_encerrados
    }
    return render(request, 'legislativo/painel_gerente.html', context)


@login_required
@require_POST
def votar(request, projeto_id):
    projeto = get_object_or_404(Projeto, pk=projeto_id)
    escolha = request.POST.get('escolha') 
    
    # 1. Validação de Abertura/Tempo
    agora = timezone.now()
    limite = projeto.abertura_voto + timedelta(seconds=projeto.tempo_limite_segundos)
    
    if projeto.status != 'ABERTO' or agora > limite:
        # Votação não está aberta ou tempo expirou
        return redirect('legislativo:painel_vereador') 

    # 2. Validação de Voto Único
    voto_existente = Voto.objects.filter(projeto=projeto, vereador=request.user).exists()
    if voto_existente:
        # Já votou
        return redirect('legislativo:painel_vereador')

    # 3. Cria e salva o voto
    Voto.objects.create(
        projeto=projeto, 
        vereador=request.user, 
        escolha=escolha
    )
    
    return redirect('legislativo:painel_vereador')

# --- 4. Ações do Gerente (Abrir/Fechar Votação) ---
def check_is_gerente(user):
    return user.groups.filter(name='Gerente de Votação').exists()

@login_required
def iniciar_votacao(request, projeto_id):
    if not check_is_gerente(request.user):
        return HttpResponseForbidden()
    
    projeto = get_object_or_404(Projeto, pk=projeto_id)
    
    # Zera votos de votações anteriores deste projeto
    Voto.objects.filter(projeto=projeto).delete()
    
    # Atualiza status e marca a hora de início
    projeto.status = 'ABERTO'
    projeto.abertura_voto = timezone.now()
    projeto.save()
    
    return redirect('legislativo:painel_vereador')


@login_required
def encerrar_votacao(request, projeto_id):
    if not check_is_gerente(request.user):
        return HttpResponseForbidden()
        
    projeto = get_object_or_404(Projeto, pk=projeto_id)
    projeto.status = 'FECHADO'
    projeto.save()
    
    return redirect('legislativo:painel_vereador')


# --- 5. API de Resultados em Tempo Real ---
def resultados_api(request, projeto_id):
    projeto = get_object_or_404(Projeto, pk=projeto_id)
    agora = timezone.now()

    # Cálculo do tempo restante
    tempo_restante = 0
    if projeto.status == 'ABERTO':
        limite = projeto.abertura_voto + timedelta(seconds=projeto.tempo_limite_segundos)
        if limite > agora:
            tempo_restante = int((limite - agora).total_seconds())
        else:
            # Tempo esgotado, mas o gerente não fechou (a API notifica a expiração)
            tempo_restante = 0 
            
    votos_computados = projeto.voto_set.count()

    # Monta os votos individuais
    votos_individuais = [{
        'vereador': voto.vereador.username,
        'escolha': voto.get_escolha_display(),
    } for voto in projeto.voto_set.all().select_related('vereador')]

    # Retorna o JSON
    return JsonResponse({
        'id': projeto.id,
        'titulo': projeto.titulo,
        'status': projeto.status,
        'tempo_restante': tempo_restante,
        'sim': projeto.votos_sim(),
        'nao': projeto.votos_nao(),
        'abstencao': projeto.votos_abstencao(),
        'votos_computados': votos_computados,
        'total_vereadores': TOTAL_VEREADORES,
        'votos_individuais': votos_individuais,
        'quorum_necessario': projeto.get_quorum_minimo_display(),
    })
    
@login_required
def painel_secretaria(request):
    if not check_is_secretaria(request.user):
        return HttpResponseForbidden("Acesso negado. Você não pertence ao grupo Secretaria Geral.")
    
    projetos = Projeto.objects.filter(status='PREPARACAO').order_by('-id')
    
    if request.method == 'POST':
        form = ProjetoForm(request.POST)
        if form.is_valid():
            projeto = form.save(commit=False)
            # O status já é 'PREPARACAO' por padrão no Model.
            projeto.save()
            return redirect('legislativo:painel_secretaria')
    else:
        form = ProjetoForm()
        
    context = {
        'form': form,
        'projetos': projetos
    }
    return render(request, 'legislativo/painel_secretaria.html', context)