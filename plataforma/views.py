from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.contrib import messages
from django.contrib.messages import constants
from django.urls import reverse
from decimal import Decimal
from .models import Pacientes, DadosPaciente, Refeicao, Opcao
from django.utils import timezone


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
        pacientes = Pacientes.objects.filter(nutri=request.user)
        return render(request, 'pacientes.html', {'pacientes': pacientes})
    elif request.method == 'POST':
        nome = request.POST.get('nome')
        sexo = request.POST.get('sexo')
        idade = request.POST.get('idade')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')

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
def dados_paciente_listar(request):
    if request.method == "GET":
        pacientes = Pacientes.objects.filter(nutri=request.user)
        return render(request, 'dados_paciente_listar.html', {'pacientes': pacientes})


@login_required(login_url='/auth/logar/')
def dados_paciente(request, id):
    paciente = get_object_or_404(Pacientes, id=id, nutri=request.user)

    if request.method == "GET":
        dados_paciente = DadosPaciente.objects.filter(paciente=paciente)
        return render(request, 'dados_paciente.html', {'paciente': paciente, 'dados_paciente': dados_paciente})

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
        pacientes = Pacientes.objects.filter(nutri=request.user)
        return render(request, 'plano_alimentar_listar.html', {'pacientes': pacientes})


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
