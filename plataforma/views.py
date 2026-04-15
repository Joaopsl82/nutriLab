import csv

from django.urls import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages
from django.contrib.messages import constants
from django.db.models import Q
from datetime import date
from decimal import Decimal

from .models import (
    AlimentoNutricional,
    AnexoExameAvaliacao,
    AnotacaoPaciente,
    AvaliacaoAntropometrica,
    DadosPaciente,
    FichaAnamnese,
    FotoAvaliacaoAntropometrica,
    GastoEnergetico,
    ItemRefeicaoAlimento,
    Opcao,
    Pacientes,
    Refeicao,
)
from django.utils import timezone

from .nutricao import (
    TOTAIS_ZERADOS,
    percentuais_energia_macros,
    sincronizar_macros_refeicao_legacy,
    somar_totais,
    totais_refeicao_mostrados,
)


SITUACOES_VALIDAS = {c[0] for c in Pacientes.choices_situacao}


def _pacientes_filtrados(user, q=None, situacao=None):
    qs = Pacientes.objects.filter(nutri=user)
    if situacao in SITUACOES_VALIDAS:
        qs = qs.filter(situacao=situacao)
    q = (q or '').strip()
    if q:
        qs = qs.filter(
            Q(nome__icontains=q) | Q(email__icontains=q) | Q(telefone__icontains=q)
        )
    return qs.order_by('nome')


def _numeric_or_none(s):
    if s is None or str(s).strip() == '':
        return None
    t = str(s).strip().replace(',', '.')
    try:
        return Decimal(t)
    except Exception:
        return None


def _int_post(s, default=0):
    try:
        t = str(s or '').strip().replace(',', '.')
        if t == '':
            return default
        return int(float(t))
    except (TypeError, ValueError):
        return default


def _parse_dados_clinicos_post(post):
    peso = _numeric_or_none(post.get('peso'))
    altura = _numeric_or_none(post.get('altura'))
    gordura = _numeric_or_none(post.get('gordura'))
    musculo = _numeric_or_none(post.get('musculo'))
    hdl = _numeric_or_none(post.get('hdl'))
    ldl = _numeric_or_none(post.get('ldl'))
    colesterol_total = _numeric_or_none(post.get('ctotal'))
    triglicer = _numeric_or_none(post.get('triglicerídios'))
    checks = [
        (peso, 'Digite um peso válido'),
        (altura, 'Digite uma altura válida'),
        (gordura, 'Digite uma gordura válida'),
        (musculo, 'Digite um percentual de músculo válido'),
        (hdl, 'Digite um HDL válido'),
        (ldl, 'Digite um LDL válido'),
        (colesterol_total, 'Digite um colesterol total válido'),
        (triglicer, 'Digite triglicerídeos válidos'),
    ]
    for val, msg in checks:
        if val is None:
            return None, msg
    return {
        'peso': peso,
        'altura': altura,
        'percentual_gordura': gordura,
        'percentual_musculo': musculo,
        'colesterol_hdl': hdl,
        'colesterol_ldl': ldl,
        'colesterol_total': colesterol_total,
        'trigliceridios': triglicer,
    }, None


def _parse_date_required(post, key='data'):
    raw = (post.get(key) or '').strip()
    if not raw:
        return None, 'Indique a data.'
    try:
        return date.fromisoformat(raw), None
    except ValueError:
        return None, 'Data inválida.'


AV_ANTROP_DECIMAL_FIELDS = (
    'altura',
    'peso_atual',
    'peso_ideal',
    'braco_dir_contraido',
    'braco_esq_contraido',
    'braco_dir_relaxado',
    'braco_esq_relaxado',
    'antebraco_dir',
    'antebraco_esq',
    'punho_dir',
    'punho_esq',
    'tronco',
    'ombro',
    'peitoral',
    'cintura',
    'abdomen',
    'quadril',
    'coxa_dir',
    'coxa_esq',
    'panturrilha_dir',
    'panturrilha_esq',
)


def _preencher_avaliacao_antropometrica_de_post(inst, post):
    inst.descricao = (post.get('descricao') or '').strip()
    inst.dobras_cutaneas = (post.get('dobras_cutaneas') or '').strip()
    inst.bioimpedancia = (post.get('bioimpedancia') or '').strip()
    for name in AV_ANTROP_DECIMAL_FIELDS:
        setattr(inst, name, _numeric_or_none(post.get(name)))


def _decimal_post(s, default=None, min_val=None, max_val=None):
    if s is None or str(s).strip() == '':
        return default
    t = str(s).strip().replace(',', '.')
    try:
        v = Decimal(t)
    except Exception:
        return default
    if min_val is not None and v < min_val:
        return default
    if max_val is not None and v > max_val:
        return default
    return v


def _alimentos_do_nutricionista(user):
    return AlimentoNutricional.objects.filter(Q(nutri__isnull=True) | Q(nutri=user)).order_by(
        'nome'
    )


def _nutri_pode_usar_alimento(user, alimento):
    return alimento.nutri_id is None or alimento.nutri_id == user.id


def _opcao_titulo_duplicado_na_refeicao(refeicao, titulo, excluir_pk=None):
    """Título não vazio e igual (sem diferenciar maiúsculas) a outra opção da mesma refeição."""
    tn = (titulo or '').strip()
    if not tn:
        return False
    qs = Opcao.objects.filter(refeicao=refeicao, titulo__iexact=tn)
    if excluir_pk is not None:
        qs = qs.exclude(pk=excluir_pk)
    return qs.exists()


def _refeicao_titulo_normalizado(titulo):
    return (titulo or '').strip()[:50] or 'Refeição'


def _refeicao_titulo_duplicado_no_paciente(paciente, titulo, excluir_pk=None):
    """Mesmo título (após normalização, sem diferenciar maiúsculas) noutra refeição do paciente."""
    tn = _refeicao_titulo_normalizado(titulo)
    qs = Refeicao.objects.filter(paciente=paciente, titulo__iexact=tn)
    if excluir_pk is not None:
        qs = qs.exclude(pk=excluir_pk)
    return qs.exists()


@login_required(login_url='/auth/logar/')
def pacientes(request):
    if request.method == 'GET':
        q = request.GET.get('q', '')
        situacao = request.GET.get('situacao', '')
        lista = _pacientes_filtrados(request.user, q=q, situacao=situacao)
        return render(
            request,
            'pacientes.html',
            {
                'pacientes': lista,
                'filtro_q': (q or '').strip(),
                'filtro_situacao': situacao if situacao in SITUACOES_VALIDAS else '',
                'situacao_choices': Pacientes.choices_situacao,
            },
        )
    elif request.method == 'POST':
        nome = request.POST.get('nome')
        sexo = request.POST.get('sexo')
        idade = request.POST.get('idade')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')
        situacao = (request.POST.get('situacao') or 'ativo').strip()
        if situacao not in SITUACOES_VALIDAS:
            situacao = 'ativo'

        if (len(nome.strip()) == 0) or (len(sexo.strip()) == 0) or (len(idade.strip()) == 0) or (len(email.strip()) == 0) or (len(telefone.strip()) == 0):
            messages.add_message(request, constants.ERROR, 'Preencha todos os campos')
            return redirect('pacientes')

        if not idade.isnumeric():
            messages.add_message(request, constants.ERROR, 'Digite uma idade válida')
            return redirect('pacientes')

        pacientes_qs = Pacientes.objects.filter(nutri=request.user, email=email)

        if pacientes_qs.exists():
            messages.add_message(request, constants.ERROR, 'Já existe um paciente com esse E-mail')
            return redirect('pacientes')

        try:
            paciente = Pacientes(
                nome=nome,
                sexo=sexo,
                idade=idade,
                email=email,
                telefone=telefone,
                situacao=situacao,
                nutri=request.user,
            )
            foto = request.FILES.get('foto')
            if foto:
                paciente.foto = foto
            paciente.save()
            messages.add_message(request, constants.SUCCESS, 'Paciente cadastrado com sucesso')
            return redirect('pacientes')
        except Exception:
            messages.add_message(request, constants.ERROR, 'Erro interno do sistema')
            return redirect('pacientes')


@login_required(login_url='/auth/logar/')
@require_POST
def paciente_editar(request, id):
    paciente = get_object_or_404(Pacientes, id=id, nutri=request.user)
    nome = (request.POST.get('nome') or '').strip()
    sexo = (request.POST.get('sexo') or '').strip()
    idade = (request.POST.get('idade') or '').strip()
    email = (request.POST.get('email') or '').strip()
    telefone = (request.POST.get('telefone') or '').strip()
    situacao = (request.POST.get('situacao') or '').strip()
    if situacao not in SITUACOES_VALIDAS:
        situacao = paciente.situacao

    if not nome or not sexo or not idade or not email or not telefone:
        messages.add_message(request, constants.ERROR, 'Preencha todos os campos')
        return redirect('pacientes')

    if not str(idade).isnumeric():
        messages.add_message(request, constants.ERROR, 'Digite uma idade válida')
        return redirect('pacientes')

    duplicado = Pacientes.objects.filter(nutri=request.user, email=email).exclude(pk=paciente.pk).exists()
    if duplicado:
        messages.add_message(request, constants.ERROR, 'Já existe outro paciente com esse e-mail')
        return redirect('pacientes')

    paciente.nome = nome
    paciente.sexo = sexo
    paciente.idade = int(str(idade))
    paciente.email = email
    paciente.telefone = telefone
    paciente.situacao = situacao

    if request.POST.get('remover_foto'):
        if paciente.foto:
            paciente.foto.delete(save=False)
        paciente.foto = None
    foto = request.FILES.get('foto')
    if foto:
        if paciente.foto:
            paciente.foto.delete(save=False)
        paciente.foto = foto

    try:
        paciente.save()
        messages.add_message(request, constants.SUCCESS, 'Dados do paciente atualizados')
    except Exception:
        messages.add_message(request, constants.ERROR, 'Não foi possível salvar as alterações')
    return redirect('pacientes')


@login_required(login_url='/auth/logar/')
@require_POST
def paciente_excluir(request, id):
    paciente = get_object_or_404(Pacientes, id=id, nutri=request.user)
    nome = paciente.nome
    paciente.delete()
    messages.add_message(request, constants.SUCCESS, f'Paciente «{nome}» removido')
    return redirect('pacientes')


@login_required(login_url='/auth/logar/')
def dados_paciente_listar(request):
    if request.method == "GET":
        q = request.GET.get('q', '')
        pacientes = _pacientes_filtrados(request.user, q=q)
        return render(
            request,
            'dados_paciente_listar.html',
            {'pacientes': pacientes, 'filtro_q': (q or '').strip()},
        )


@login_required(login_url='/auth/logar/')
def dados_paciente(request, id):
    paciente = get_object_or_404(Pacientes, id=id, nutri=request.user)

    if request.method == "GET":
        fichas_anamnese = FichaAnamnese.objects.filter(
            paciente=paciente,
            nutri=request.user,
        )
        avaliacoes_antropometricas = (
            AvaliacaoAntropometrica.objects.filter(paciente=paciente, nutri=request.user)
            .prefetch_related('fotos', 'anexos_exames')
            .order_by('-data', '-id')
        )
        gastos_energeticos = GastoEnergetico.objects.filter(
            paciente=paciente,
            nutri=request.user,
        )
        dados_paciente = DadosPaciente.objects.filter(paciente=paciente).order_by('-data')
        anotacoes = AnotacaoPaciente.objects.filter(paciente=paciente, nutri=request.user)
        ultimo_dado = dados_paciente.first()
        diff_meta = None
        if paciente.peso_meta is not None and ultimo_dado is not None:
            diff_meta = ultimo_dado.peso - paciente.peso_meta

        dados_clinicos_edit_data = [
            {
                'id': d.id,
                'peso': str(d.peso),
                'altura': str(d.altura),
                'gordura': str(d.percentual_gordura),
                'musculo': str(d.percentual_musculo),
                'hdl': str(d.colesterol_hdl),
                'ldl': str(d.colesterol_ldl),
                'ctotal': str(d.colesterol_total),
                'triglicer': str(d.trigliceridios),
                'edit_url': reverse(
                    'dado_clinico_editar',
                    kwargs={'id': paciente.id, 'dado_id': d.id},
                ),
            }
            for d in dados_paciente
        ]
        anotacoes_edit_data = [
            {
                'id': a.id,
                'texto': a.texto,
                'edit_url': reverse(
                    'anotacao_editar',
                    kwargs={'id': paciente.id, 'anotacao_id': a.id},
                ),
            }
            for a in anotacoes
        ]
        fichas_anamnese_edit_data = [
            {
                'id': f.id,
                'conteudo': f.conteudo,
                'edit_url': reverse(
                    'anamnese_editar',
                    kwargs={'id': paciente.id, 'ficha_id': f.id},
                ),
            }
            for f in fichas_anamnese
        ]

        return render(
            request,
            'dados_paciente.html',
            {
                'paciente': paciente,
                'fichas_anamnese': fichas_anamnese,
                'avaliacoes_antropometricas': avaliacoes_antropometricas,
                'gastos_energeticos': gastos_energeticos,
                'dados_paciente': dados_paciente,
                'anotacoes': anotacoes,
                'ultimo_dado': ultimo_dado,
                'diff_meta': diff_meta,
                'dados_clinicos_edit_data': dados_clinicos_edit_data,
                'anotacoes_edit_data': anotacoes_edit_data,
                'fichas_anamnese_edit_data': fichas_anamnese_edit_data,
            },
        )

    if request.method == "POST":
        parsed, err = _parse_dados_clinicos_post(request.POST)
        if err:
            messages.add_message(request, constants.ERROR, err)
            return redirect('dados_paciente', id=paciente.id)

        DadosPaciente.objects.create(
            paciente=paciente,
            data=timezone.now(),
            peso=parsed['peso'],
            altura=parsed['altura'],
            percentual_gordura=parsed['percentual_gordura'],
            percentual_musculo=parsed['percentual_musculo'],
            colesterol_hdl=parsed['colesterol_hdl'],
            colesterol_ldl=parsed['colesterol_ldl'],
            colesterol_total=parsed['colesterol_total'],
            trigliceridios=parsed['trigliceridios'],
        )
        messages.add_message(request, constants.SUCCESS, 'Dados cadastrados com sucesso')
        return redirect('dados_paciente', id=paciente.id)


@login_required(login_url='/auth/logar/')
@require_POST
def paciente_peso_meta(request, id):
    paciente = get_object_or_404(Pacientes, id=id, nutri=request.user)
    if request.POST.get('limpar_meta'):
        paciente.peso_meta = None
        paciente.save(update_fields=['peso_meta'])
        messages.add_message(request, constants.SUCCESS, 'Meta de peso removida.')
        return redirect('dados_paciente', id=paciente.id)
    raw = (request.POST.get('peso_meta') or '').strip()
    if raw == '':
        messages.add_message(request, constants.ERROR, 'Indique um peso meta (kg) ou use «Remover meta».')
        return redirect('dados_paciente', id=paciente.id)
    v = _numeric_or_none(raw)
    if v is None:
        messages.add_message(request, constants.ERROR, 'Indique um peso meta válido.')
        return redirect('dados_paciente', id=paciente.id)
    paciente.peso_meta = v
    paciente.save(update_fields=['peso_meta'])
    messages.add_message(request, constants.SUCCESS, 'Meta de peso atualizada.')
    return redirect('dados_paciente', id=paciente.id)


@login_required(login_url='/auth/logar/')
@require_POST
def anotacao_adicionar(request, id):
    paciente = get_object_or_404(Pacientes, id=id, nutri=request.user)
    texto = (request.POST.get('texto') or '').strip()
    if not texto:
        messages.add_message(request, constants.ERROR, 'Escreva a anotação antes de salvar.')
        return redirect('dados_paciente', id=paciente.id)
    if len(texto) > 2000:
        messages.add_message(request, constants.ERROR, 'Anotação demasiado longa (máx. 2000 caracteres).')
        return redirect('dados_paciente', id=paciente.id)
    AnotacaoPaciente.objects.create(paciente=paciente, nutri=request.user, texto=texto)
    messages.add_message(request, constants.SUCCESS, 'Anotação registada.')
    return redirect('dados_paciente', id=paciente.id)


@login_required(login_url='/auth/logar/')
@require_POST
def dado_clinico_editar(request, id, dado_id):
    paciente = get_object_or_404(Pacientes, id=id, nutri=request.user)
    dado = get_object_or_404(DadosPaciente, id=dado_id, paciente=paciente)
    parsed, err = _parse_dados_clinicos_post(request.POST)
    if err:
        messages.add_message(request, constants.ERROR, err)
        return redirect('dados_paciente', id=paciente.id)

    dado.data = timezone.now()
    dado.peso = parsed['peso']
    dado.altura = parsed['altura']
    dado.percentual_gordura = parsed['percentual_gordura']
    dado.percentual_musculo = parsed['percentual_musculo']
    dado.colesterol_hdl = parsed['colesterol_hdl']
    dado.colesterol_ldl = parsed['colesterol_ldl']
    dado.colesterol_total = parsed['colesterol_total']
    dado.trigliceridios = parsed['trigliceridios']
    dado.save()
    messages.add_message(request, constants.SUCCESS, 'Registo clínico atualizado.')
    return redirect('dados_paciente', id=paciente.id)


@login_required(login_url='/auth/logar/')
@require_POST
def dado_clinico_excluir(request, id, dado_id):
    paciente = get_object_or_404(Pacientes, id=id, nutri=request.user)
    dado = get_object_or_404(DadosPaciente, id=dado_id, paciente=paciente)
    dado.delete()
    messages.add_message(request, constants.SUCCESS, 'Registo clínico removido.')
    return redirect('dados_paciente', id=paciente.id)


@login_required(login_url='/auth/logar/')
@require_POST
def anotacao_editar(request, id, anotacao_id):
    paciente = get_object_or_404(Pacientes, id=id, nutri=request.user)
    anot = get_object_or_404(
        AnotacaoPaciente,
        id=anotacao_id,
        paciente=paciente,
        nutri=request.user,
    )
    texto = (request.POST.get('texto') or '').strip()
    if not texto:
        messages.add_message(request, constants.ERROR, 'Escreva a anotação antes de salvar.')
        return redirect('dados_paciente', id=paciente.id)
    if len(texto) > 2000:
        messages.add_message(request, constants.ERROR, 'Anotação demasiado longa (máx. 2000 caracteres).')
        return redirect('dados_paciente', id=paciente.id)
    anot.texto = texto
    anot.criado_em = timezone.now()
    anot.save(update_fields=['texto', 'criado_em'])
    messages.add_message(request, constants.SUCCESS, 'Anotação atualizada.')
    return redirect('dados_paciente', id=paciente.id)


@login_required(login_url='/auth/logar/')
@require_POST
def anotacao_excluir(request, id, anotacao_id):
    paciente = get_object_or_404(Pacientes, id=id, nutri=request.user)
    anot = get_object_or_404(
        AnotacaoPaciente,
        id=anotacao_id,
        paciente=paciente,
        nutri=request.user,
    )
    anot.delete()
    messages.add_message(request, constants.SUCCESS, 'Anotação removida.')
    return redirect('dados_paciente', id=paciente.id)


@login_required(login_url='/auth/logar/')
@require_POST
def anamnese_adicionar(request, id):
    paciente = get_object_or_404(Pacientes, id=id, nutri=request.user)
    texto = (request.POST.get('conteudo') or '').strip()
    if not texto:
        messages.add_message(request, constants.ERROR, 'Preencha o conteúdo da ficha de anamnese.')
        return redirect('dados_paciente', id=paciente.id)
    if len(texto) > 20000:
        messages.add_message(request, constants.ERROR, 'Texto demasiado longo (máx. 20000 caracteres).')
        return redirect('dados_paciente', id=paciente.id)
    FichaAnamnese.objects.create(paciente=paciente, nutri=request.user, conteudo=texto)
    messages.add_message(request, constants.SUCCESS, 'Ficha de anamnese registada.')
    return redirect('dados_paciente', id=paciente.id)


@login_required(login_url='/auth/logar/')
@require_POST
def anamnese_editar(request, id, ficha_id):
    paciente = get_object_or_404(Pacientes, id=id, nutri=request.user)
    ficha = get_object_or_404(
        FichaAnamnese,
        id=ficha_id,
        paciente=paciente,
        nutri=request.user,
    )
    texto = (request.POST.get('conteudo') or '').strip()
    if not texto:
        messages.add_message(request, constants.ERROR, 'Preencha o conteúdo da ficha de anamnese.')
        return redirect('dados_paciente', id=paciente.id)
    if len(texto) > 20000:
        messages.add_message(request, constants.ERROR, 'Texto demasiado longo (máx. 20000 caracteres).')
        return redirect('dados_paciente', id=paciente.id)
    ficha.conteudo = texto
    ficha.save()
    messages.add_message(request, constants.SUCCESS, 'Ficha de anamnese atualizada.')
    return redirect('dados_paciente', id=paciente.id)


@login_required(login_url='/auth/logar/')
@require_POST
def anamnese_excluir(request, id, ficha_id):
    paciente = get_object_or_404(Pacientes, id=id, nutri=request.user)
    ficha = get_object_or_404(
        FichaAnamnese,
        id=ficha_id,
        paciente=paciente,
        nutri=request.user,
    )
    ficha.delete()
    messages.add_message(request, constants.SUCCESS, 'Ficha de anamnese removida.')
    return redirect('dados_paciente', id=paciente.id)


@login_required(login_url='/auth/logar/')
def avaliacao_antropometrica_nova(request, id):
    paciente = get_object_or_404(Pacientes, id=id, nutri=request.user)
    if request.method == 'GET':
        return render(
            request,
            'avaliacao_antropometrica_form.html',
            {'paciente': paciente, 'avaliacao': None},
        )
    d, err = _parse_date_required(request.POST)
    if err:
        messages.add_message(request, constants.ERROR, err)
        return redirect('avaliacao_antropometrica_nova', id=paciente.id)
    av = AvaliacaoAntropometrica(
        paciente=paciente,
        nutri=request.user,
        data=d,
    )
    _preencher_avaliacao_antropometrica_de_post(av, request.POST)
    av.save()
    for f in request.FILES.getlist('fotos'):
        if f:
            FotoAvaliacaoAntropometrica.objects.create(avaliacao=av, imagem=f)
    for f in request.FILES.getlist('anexos_exames'):
        if f:
            AnexoExameAvaliacao.objects.create(avaliacao=av, arquivo=f)
    messages.add_message(request, constants.SUCCESS, 'Avaliação antropométrica registada.')
    return redirect('dados_paciente', id=paciente.id)


@login_required(login_url='/auth/logar/')
def avaliacao_antropometrica_editar(request, id, av_id):
    paciente = get_object_or_404(Pacientes, id=id, nutri=request.user)
    av = get_object_or_404(
        AvaliacaoAntropometrica,
        id=av_id,
        paciente=paciente,
        nutri=request.user,
    )
    if request.method == 'GET':
        return render(
            request,
            'avaliacao_antropometrica_form.html',
            {'paciente': paciente, 'avaliacao': av},
        )
    d, err = _parse_date_required(request.POST)
    if err:
        messages.add_message(request, constants.ERROR, err)
        return redirect('avaliacao_antropometrica_editar', id=paciente.id, av_id=av.id)
    av.data = d
    _preencher_avaliacao_antropometrica_de_post(av, request.POST)
    av.save()
    for f in request.FILES.getlist('fotos'):
        if f:
            FotoAvaliacaoAntropometrica.objects.create(avaliacao=av, imagem=f)
    for f in request.FILES.getlist('anexos_exames'):
        if f:
            AnexoExameAvaliacao.objects.create(avaliacao=av, arquivo=f)
    messages.add_message(request, constants.SUCCESS, 'Avaliação antropométrica atualizada.')
    return redirect('dados_paciente', id=paciente.id)


@login_required(login_url='/auth/logar/')
@require_POST
def avaliacao_antropometrica_excluir(request, id, av_id):
    paciente = get_object_or_404(Pacientes, id=id, nutri=request.user)
    av = get_object_or_404(
        AvaliacaoAntropometrica,
        id=av_id,
        paciente=paciente,
        nutri=request.user,
    )
    for foto in av.fotos.all():
        if foto.imagem:
            foto.imagem.delete(save=False)
        foto.delete()
    for anexo in av.anexos_exames.all():
        if anexo.arquivo:
            anexo.arquivo.delete(save=False)
        anexo.delete()
    av.delete()
    messages.add_message(request, constants.SUCCESS, 'Avaliação antropométrica removida.')
    return redirect('dados_paciente', id=paciente.id)


@login_required(login_url='/auth/logar/')
def gasto_energetico_nova(request, id):
    paciente = get_object_or_404(Pacientes, id=id, nutri=request.user)
    if request.method == 'GET':
        return render(
            request,
            'gasto_energetico_form.html',
            {'paciente': paciente, 'gasto': None},
        )
    d, err = _parse_date_required(request.POST)
    if err:
        messages.add_message(request, constants.ERROR, err)
        return redirect('gasto_energetico_nova', id=paciente.id)
    ge = GastoEnergetico(paciente=paciente, nutri=request.user, data=d)
    ge.descricao = (request.POST.get('descricao') or '').strip()
    ge.calculos_protocolos = (request.POST.get('calculos_protocolos') or '').strip()
    ge.nivel_atividade_met = (request.POST.get('nivel_atividade_met') or '').strip()
    ge.atividades_fisicas = (request.POST.get('atividades_fisicas') or '').strip()
    ge.resultados = (request.POST.get('resultados') or '').strip()
    ge.altura = _numeric_or_none(request.POST.get('altura'))
    ge.peso = _numeric_or_none(request.POST.get('peso'))
    ge.fator_lesao = _numeric_or_none(request.POST.get('fator_lesao'))
    ge.massa_magra_kg = _numeric_or_none(request.POST.get('massa_magra_kg'))
    ge.save()
    messages.add_message(request, constants.SUCCESS, 'Gasto energético registado.')
    return redirect('dados_paciente', id=paciente.id)


@login_required(login_url='/auth/logar/')
def gasto_energetico_editar(request, id, ge_id):
    paciente = get_object_or_404(Pacientes, id=id, nutri=request.user)
    ge = get_object_or_404(
        GastoEnergetico,
        id=ge_id,
        paciente=paciente,
        nutri=request.user,
    )
    if request.method == 'GET':
        return render(
            request,
            'gasto_energetico_form.html',
            {'paciente': paciente, 'gasto': ge},
        )
    d, err = _parse_date_required(request.POST)
    if err:
        messages.add_message(request, constants.ERROR, err)
        return redirect('gasto_energetico_editar', id=paciente.id, ge_id=ge.id)
    ge.data = d
    ge.descricao = (request.POST.get('descricao') or '').strip()
    ge.calculos_protocolos = (request.POST.get('calculos_protocolos') or '').strip()
    ge.nivel_atividade_met = (request.POST.get('nivel_atividade_met') or '').strip()
    ge.atividades_fisicas = (request.POST.get('atividades_fisicas') or '').strip()
    ge.resultados = (request.POST.get('resultados') or '').strip()
    ge.altura = _numeric_or_none(request.POST.get('altura'))
    ge.peso = _numeric_or_none(request.POST.get('peso'))
    ge.fator_lesao = _numeric_or_none(request.POST.get('fator_lesao'))
    ge.massa_magra_kg = _numeric_or_none(request.POST.get('massa_magra_kg'))
    ge.save()
    messages.add_message(request, constants.SUCCESS, 'Gasto energético atualizado.')
    return redirect('dados_paciente', id=paciente.id)


@login_required(login_url='/auth/logar/')
@require_POST
def gasto_energetico_excluir(request, id, ge_id):
    paciente = get_object_or_404(Pacientes, id=id, nutri=request.user)
    ge = get_object_or_404(
        GastoEnergetico,
        id=ge_id,
        paciente=paciente,
        nutri=request.user,
    )
    ge.delete()
    messages.add_message(request, constants.SUCCESS, 'Gasto energético removido.')
    return redirect('dados_paciente', id=paciente.id)


@login_required(login_url='/auth/logar/')
@require_GET
def dados_paciente_export_csv(request, id):
    paciente = get_object_or_404(Pacientes, id=id, nutri=request.user)
    dados = DadosPaciente.objects.filter(paciente=paciente).order_by('data')
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    safe_name = ''.join(c if c.isalnum() or c in '-_' else '_' for c in paciente.nome[:40])
    response['Content-Disposition'] = f'attachment; filename="dados_clinicos_{safe_name}_{paciente.id}.csv"'
    response.write('\ufeff')
    w = csv.writer(response)
    w.writerow(
        [
            'Data',
            'Peso_kg',
            'Altura_cm',
            'Pct_gordura',
            'Pct_musculo',
            'HDL_mgdL',
            'LDL_mgdL',
            'Colesterol_total_mgdL',
            'Triglicerideos_mgdL',
        ]
    )
    for d in dados:
        w.writerow(
            [
                d.data.isoformat(),
                d.peso,
                d.altura,
                d.percentual_gordura,
                d.percentual_musculo,
                d.colesterol_hdl,
                d.colesterol_ldl,
                d.colesterol_total,
                d.trigliceridios,
            ]
        )
    return response


@login_required(login_url='/auth/logar/')
@require_GET
def grafico_peso(request, id):
    paciente = get_object_or_404(Pacientes, id=id, nutri=request.user)
    dados = DadosPaciente.objects.filter(paciente=paciente).order_by("data")
    pesos = [float(dado.peso) for dado in dados]
    labels = list(range(len(pesos)))
    return JsonResponse({'peso': pesos, 'labels': labels})


@login_required(login_url='/auth/logar/')
def plano_alimentar_listar(request):
    if request.method == "GET":
        q = request.GET.get('q', '')
        pacientes = _pacientes_filtrados(request.user, q=q)
        return render(
            request,
            'plano_alimentar_listar.html',
            {'pacientes': pacientes, 'filtro_q': (q or '').strip()},
        )


@login_required(login_url='/auth/logar/')
def plano_alimentar(request, id):
    paciente = get_object_or_404(Pacientes, id=id, nutri=request.user)

    if request.method == "GET":
        refeicoes = list(
            Refeicao.objects.filter(paciente=paciente).order_by('horario', 'id')
        )
        opcoes = Opcao.objects.filter(refeicao__paciente=paciente).select_related('refeicao')
        alimentos_select = _alimentos_do_nutricionista(request.user)

        refeicoes_ctx = []
        totais_dia = {k: v for k, v in TOTAIS_ZERADOS.items()}
        for r in refeicoes:
            itens = list(
                ItemRefeicaoAlimento.objects.filter(refeicao=r).select_related('alimento')
            )
            tr = totais_refeicao_mostrados(r, itens)
            totais_dia = somar_totais(totais_dia, tr)
            refeicoes_ctx.append({'re': r, 'itens': itens, 'totais': tr})

        macro_pct = None
        macro_chart_data = None
        if refeicoes:
            macro_pct = percentuais_energia_macros(
                totais_dia['carboidratos_g'],
                totais_dia['proteinas_g'],
                totais_dia['gorduras_g'],
            )
            if macro_pct:
                macro_chart_data = {
                    'labels': ['Carboidratos', 'Proteínas', 'Gorduras'],
                    'data': [
                        macro_pct['carboidratos'],
                        macro_pct['proteinas'],
                        macro_pct['gorduras'],
                    ],
                    'kcal_dia': float(totais_dia['kcal']),
                }

        opcoes_edit_data = [
            {
                'id': o.id,
                'titulo': o.titulo or '',
                'descricao': o.descricao or '',
                'tem_imagem': bool(o.imagem),
            }
            for o in Opcao.objects.filter(refeicao__paciente=paciente).order_by('refeicao_id', 'id')
        ]

        _pid = 2147483647
        opcao_edit_url_placeholder = reverse(
            'opcao_editar',
            kwargs={'id_paciente': paciente.id, 'opcao_id': _pid},
        ).replace(f'/{_pid}/', '/__NL_OPC__/')

        refeicoes_edit_data = [
            {
                'id': r.id,
                'titulo': r.titulo,
                'horario': r.horario.strftime('%H:%M') if r.horario else '12:00',
                'carboidratos': r.carboidratos,
                'proteinas': r.proteinas,
                'gorduras': r.gorduras,
                'edit_url': reverse(
                    'refeicao_editar',
                    kwargs={'id_paciente': paciente.id, 'refeicao_id': r.id},
                ),
            }
            for r in refeicoes
        ]

        return render(
            request,
            'plano_alimentar.html',
            {
                'paciente': paciente,
                'refeicoes_ctx': refeicoes_ctx,
                'opcao': opcoes,
                'alimentos_select': alimentos_select,
                'totais_dia': totais_dia,
                'macro_pct': macro_pct,
                'macro_chart_data': macro_chart_data,
                'opcoes_edit_data': opcoes_edit_data,
                'opcao_edit_url_placeholder': opcao_edit_url_placeholder,
                'refeicoes_edit_data': refeicoes_edit_data,
            },
        )

    messages.add_message(
        request,
        constants.ERROR,
        'Este formulário não pode ser enviado por aqui. Use «Guardar alterações» no modal de editar opção ou os botões da página.',
    )
    return redirect('plano_alimentar', id=id)


@login_required(login_url='/auth/logar/')
def refeicao(request, id_paciente):
    paciente = get_object_or_404(Pacientes, id=id_paciente, nutri=request.user)

    if request.method == "POST":
        titulo = request.POST.get('titulo')
        horario = request.POST.get('horario')
        carboidratos = request.POST.get('carboidratos')
        proteinas = request.POST.get('proteinas')
        gorduras = request.POST.get('gorduras')

        titulo_norm = _refeicao_titulo_normalizado(titulo)
        if _refeicao_titulo_duplicado_no_paciente(paciente, titulo_norm):
            messages.add_message(
                request,
                constants.ERROR,
                'Já existe uma refeição com este título para este paciente. Escolha outro título.',
            )
            return redirect('plano_alimentar', id=id_paciente)

        Refeicao.objects.create(
            paciente=paciente,
            titulo=titulo_norm,
            horario=horario or '12:00',
            carboidratos=_int_post(carboidratos, 0),
            proteinas=_int_post(proteinas, 0),
            gorduras=_int_post(gorduras, 0),
        )
        messages.add_message(request, constants.SUCCESS, 'Refeição cadastrada')
        return redirect('plano_alimentar', id=id_paciente)

    return redirect('plano_alimentar', id=id_paciente)


@login_required(login_url='/auth/logar/')
@require_POST
def refeicao_editar(request, id_paciente, refeicao_id):
    paciente = get_object_or_404(Pacientes, id=id_paciente, nutri=request.user)
    ref = get_object_or_404(Refeicao, id=refeicao_id, paciente=paciente)
    titulo = request.POST.get('titulo')
    horario = request.POST.get('horario')
    carboidratos = request.POST.get('carboidratos')
    proteinas = request.POST.get('proteinas')
    gorduras = request.POST.get('gorduras')

    titulo_norm = _refeicao_titulo_normalizado(titulo)
    if _refeicao_titulo_duplicado_no_paciente(paciente, titulo_norm, excluir_pk=ref.pk):
        messages.add_message(
            request,
            constants.ERROR,
            'Já existe uma refeição com este título para este paciente. Escolha outro título.',
        )
        return redirect('plano_alimentar', id=id_paciente)

    ref.titulo = titulo_norm
    ref.horario = horario or ref.horario or '12:00'
    ref.carboidratos = _int_post(carboidratos, 0)
    ref.proteinas = _int_post(proteinas, 0)
    ref.gorduras = _int_post(gorduras, 0)
    ref.save()
    messages.add_message(request, constants.SUCCESS, 'Refeição atualizada.')
    return redirect('plano_alimentar', id=id_paciente)


@login_required(login_url='/auth/logar/')
@require_POST
def refeicao_excluir(request, id_paciente, refeicao_id):
    paciente = get_object_or_404(Pacientes, id=id_paciente, nutri=request.user)
    ref = get_object_or_404(Refeicao, id=refeicao_id, paciente=paciente)
    ref.delete()
    messages.add_message(request, constants.SUCCESS, 'Refeição removida.')
    return redirect('plano_alimentar', id=id_paciente)


@login_required(login_url='/auth/logar/')
def opcao(request, id_paciente):
    paciente = get_object_or_404(Pacientes, id=id_paciente, nutri=request.user)

    if request.method == "POST":
        id_refeicao = request.POST.get('refeicao')
        imagem = request.FILES.get('imagem')
        descricao = (request.POST.get('descricao') or '').strip()
        titulo = (request.POST.get('titulo') or '').strip()[:120]

        if not id_refeicao:
            messages.add_message(request, constants.ERROR, 'Selecione uma refeição')
            return redirect('plano_alimentar', id=id_paciente)

        refeicao_obj = get_object_or_404(Refeicao, id=id_refeicao, paciente=paciente)

        if not imagem and not descricao and not titulo:
            messages.add_message(
                request,
                constants.ERROR,
                'Indique um título, uma descrição e/ou uma imagem para a opção.',
            )
            return redirect('plano_alimentar', id=id_paciente)

        if _opcao_titulo_duplicado_na_refeicao(refeicao_obj, titulo):
            messages.add_message(
                request,
                constants.ERROR,
                'Já existe uma opção com este título nesta refeição. Escolha outro título.',
            )
            return redirect('plano_alimentar', id=id_paciente)

        Opcao.objects.create(
            refeicao=refeicao_obj,
            titulo=titulo,
            imagem=imagem if imagem else None,
            descricao=descricao,
        )
        messages.add_message(request, constants.SUCCESS, 'Opção cadastrada')
        return redirect('plano_alimentar', id=id_paciente)

    return redirect('plano_alimentar', id=id_paciente)


@login_required(login_url='/auth/logar/')
@require_POST
def opcao_editar(request, id_paciente, opcao_id):
    paciente = get_object_or_404(Pacientes, id=id_paciente, nutri=request.user)
    opc = get_object_or_404(Opcao, id=opcao_id, refeicao__paciente=paciente)
    descricao = (request.POST.get('descricao') or '').strip()
    titulo = (request.POST.get('titulo') or '').strip()[:120]
    nova = request.FILES.get('imagem')
    remover = bool(request.POST.get('remover_imagem'))

    if _opcao_titulo_duplicado_na_refeicao(opc.refeicao, titulo, excluir_pk=opc.pk):
        messages.add_message(
            request,
            constants.ERROR,
            'Já existe uma opção com este título nesta refeição. Escolha outro título.',
        )
        return redirect('plano_alimentar', id=id_paciente)

    tera_imagem = bool(nova) or (not remover and bool(opc.imagem))
    if not titulo and not descricao and not tera_imagem:
        messages.add_message(
            request,
            constants.ERROR,
            'A opção precisa de título, texto e/ou imagem.',
        )
        return redirect('plano_alimentar', id=id_paciente)

    if remover:
        if opc.imagem:
            opc.imagem.delete(save=False)
        opc.imagem = None

    if nova:
        if opc.imagem:
            opc.imagem.delete(save=False)
        opc.imagem = nova

    opc.titulo = titulo
    opc.descricao = descricao

    opc.save()
    messages.add_message(request, constants.SUCCESS, 'Opção atualizada.')
    return redirect('plano_alimentar', id=id_paciente)


@login_required(login_url='/auth/logar/')
@require_POST
def opcao_excluir(request, id_paciente, opcao_id):
    paciente = get_object_or_404(Pacientes, id=id_paciente, nutri=request.user)
    opc = get_object_or_404(Opcao, id=opcao_id, refeicao__paciente=paciente)
    if opc.imagem:
        opc.imagem.delete(save=False)
    opc.delete()
    messages.add_message(request, constants.SUCCESS, 'Opção removida.')
    return redirect('plano_alimentar', id=id_paciente)


@login_required(login_url='/auth/logar/')
@require_POST
def item_refeicao_adicionar(request, id_paciente):
    paciente = get_object_or_404(Pacientes, id=id_paciente, nutri=request.user)
    refeicao_obj = get_object_or_404(
        Refeicao,
        id=request.POST.get('refeicao_id'),
        paciente=paciente,
    )
    alimento = get_object_or_404(AlimentoNutricional, id=request.POST.get('alimento_id'))
    if not _nutri_pode_usar_alimento(request.user, alimento):
        messages.add_message(request, constants.ERROR, 'Não pode usar este alimento.')
        return redirect('plano_alimentar', id=id_paciente)
    qtd = _decimal_post(request.POST.get('quantidade_gramas'), min_val=Decimal('0.01'), max_val=Decimal('5000'))
    if qtd is None:
        messages.add_message(
            request,
            constants.ERROR,
            'Indique uma quantidade em gramas válida (entre 0,01 e 5000).',
        )
        return redirect('plano_alimentar', id=id_paciente)

    ItemRefeicaoAlimento.objects.create(
        refeicao=refeicao_obj,
        alimento=alimento,
        quantidade_gramas=qtd,
    )
    sincronizar_macros_refeicao_legacy(refeicao_obj)
    messages.add_message(request, constants.SUCCESS, f'«{alimento.nome}» adicionado à refeição.')
    return redirect('plano_alimentar', id=id_paciente)


@login_required(login_url='/auth/logar/')
@require_POST
def item_refeicao_remover(request, id_paciente, item_id):
    paciente = get_object_or_404(Pacientes, id=id_paciente, nutri=request.user)
    item = get_object_or_404(
        ItemRefeicaoAlimento,
        id=item_id,
        refeicao__paciente=paciente,
    )
    ref = item.refeicao
    nome = item.alimento.nome
    item.delete()
    sincronizar_macros_refeicao_legacy(ref)
    messages.add_message(request, constants.SUCCESS, f'«{nome}» removido.')
    return redirect('plano_alimentar', id=id_paciente)


@login_required(login_url='/auth/logar/')
@require_POST
def alimento_custom_criar(request, id_paciente):
    get_object_or_404(Pacientes, id=id_paciente, nutri=request.user)
    nome = (request.POST.get('nome') or '').strip()
    if len(nome) < 2:
        messages.add_message(request, constants.ERROR, 'Indique um nome com pelo menos 2 caracteres.')
        return redirect('plano_alimentar', id=id_paciente)

    if AlimentoNutricional.objects.filter(nutri=request.user, nome__iexact=nome).exists():
        messages.add_message(
            request,
            constants.ERROR,
            'Já existe um alimento ou prato seu com esse nome.',
        )
        return redirect('plano_alimentar', id=id_paciente)

    def nutri_field(key):
        v = _decimal_post(request.POST.get(key), default=Decimal('0'), min_val=Decimal('0'), max_val=Decimal('9999'))
        return v if v is not None else Decimal('0')

    AlimentoNutricional.objects.create(
        nutri=request.user,
        nome=nome[:120],
        eh_prato=request.POST.get('eh_prato') == '1',
        kcal_100g=nutri_field('kcal_100g'),
        carboidratos_g_100g=nutri_field('carboidratos_g_100g'),
        proteinas_g_100g=nutri_field('proteinas_g_100g'),
        gorduras_g_100g=nutri_field('gorduras_g_100g'),
        fibra_g_100g=nutri_field('fibra_g_100g'),
        sodio_mg_100g=nutri_field('sodio_mg_100g'),
        calcio_mg_100g=nutri_field('calcio_mg_100g'),
        ferro_mg_100g=nutri_field('ferro_mg_100g'),
    )
    messages.add_message(request, constants.SUCCESS, f'Alimento «{nome}» guardado na sua biblioteca.')
    return redirect('plano_alimentar', id=id_paciente)
