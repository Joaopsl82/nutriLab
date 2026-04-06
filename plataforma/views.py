import csv

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages
from django.contrib.messages import constants
from django.db.models import Q
from decimal import Decimal
from .models import Pacientes, DadosPaciente, Refeicao, Opcao, AnotacaoPaciente
from django.utils import timezone


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
        dados_paciente = DadosPaciente.objects.filter(paciente=paciente).order_by('-data')
        anotacoes = AnotacaoPaciente.objects.filter(paciente=paciente, nutri=request.user)
        ultimo_dado = dados_paciente.first()
        diff_meta = None
        if paciente.peso_meta is not None and ultimo_dado is not None:
            diff_meta = ultimo_dado.peso - paciente.peso_meta
        return render(
            request,
            'dados_paciente.html',
            {
                'paciente': paciente,
                'dados_paciente': dados_paciente,
                'anotacoes': anotacoes,
                'ultimo_dado': ultimo_dado,
                'diff_meta': diff_meta,
            },
        )

    if request.method == "POST":
        peso = _numeric_or_none(request.POST.get('peso'))
        altura = _numeric_or_none(request.POST.get('altura'))
        gordura = _numeric_or_none(request.POST.get('gordura'))
        musculo = _numeric_or_none(request.POST.get('musculo'))
        hdl = _numeric_or_none(request.POST.get('hdl'))
        ldl = _numeric_or_none(request.POST.get('ldl'))
        colesterol_total = _numeric_or_none(request.POST.get('ctotal'))
        triglicer = _numeric_or_none(request.POST.get('triglicerídios'))

        def fail(msg):
            messages.add_message(request, constants.ERROR, msg)
            return redirect('dados_paciente', id=paciente.id)

        if peso is None:
            return fail('Digite um peso válido')
        if altura is None:
            return fail('Digite uma altura válida')
        if gordura is None:
            return fail('Digite uma gordura válida')
        if musculo is None:
            return fail('Digite um percentual de músculo válido')
        if hdl is None:
            return fail('Digite um HDL válido')
        if ldl is None:
            return fail('Digite um LDL válido')
        if colesterol_total is None:
            return fail('Digite um colesterol total válido')
        if triglicer is None:
            return fail('Digite triglicerídeos válidos')

        DadosPaciente.objects.create(
            paciente=paciente,
            data=timezone.now(),
            peso=peso,
            altura=altura,
            percentual_gordura=gordura,
            percentual_musculo=musculo,
            colesterol_hdl=hdl,
            colesterol_ldl=ldl,
            colesterol_total=colesterol_total,
            trigliceridios=triglicer,
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
        refeicoes = Refeicao.objects.filter(paciente=paciente)
        opcoes = Opcao.objects.filter(refeicao__paciente=paciente).select_related('refeicao')
        return render(request, 'plano_alimentar.html', {'paciente': paciente, 'refeicao': refeicoes, 'opcao': opcoes})


@login_required(login_url='/auth/logar/')
def refeicao(request, id_paciente):
    paciente = get_object_or_404(Pacientes, id=id_paciente, nutri=request.user)

    if request.method == "POST":
        titulo = request.POST.get('titulo')
        horario = request.POST.get('horario')
        carboidratos = request.POST.get('carboidratos')
        proteinas = request.POST.get('proteinas')
        gorduras = request.POST.get('gorduras')

        Refeicao.objects.create(
            paciente=paciente,
            titulo=titulo,
            horario=horario,
            carboidratos=carboidratos,
            proteinas=proteinas,
            gorduras=gorduras,
        )
        messages.add_message(request, constants.SUCCESS, 'Refeição cadastrada')
        return redirect('plano_alimentar', id=id_paciente)


@login_required(login_url='/auth/logar/')
def opcao(request, id_paciente):
    paciente = get_object_or_404(Pacientes, id=id_paciente, nutri=request.user)

    if request.method == "POST":
        id_refeicao = request.POST.get('refeicao')
        imagem = request.FILES.get('imagem')
        descricao = request.POST.get("descricao")

        if not id_refeicao:
            messages.add_message(request, constants.ERROR, 'Selecione uma refeição')
            return redirect('plano_alimentar', id=id_paciente)

        refeicao_obj = get_object_or_404(Refeicao, id=id_refeicao, paciente=paciente)

        if not imagem:
            messages.add_message(request, constants.ERROR, 'Envie uma imagem')
            return redirect('plano_alimentar', id=id_paciente)

        Opcao.objects.create(
            refeicao=refeicao_obj,
            imagem=imagem,
            descricao=descricao or '',
        )
        messages.add_message(request, constants.SUCCESS, 'Opção cadastrada')
        return redirect('plano_alimentar', id=id_paciente)
