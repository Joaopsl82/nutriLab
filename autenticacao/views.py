import os
from hashlib import sha256

from django.conf import settings
from django.contrib import auth
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.messages import constants
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import Ativacao
from .utils import email_html, password_is_valid


def home(request):
    if request.user.is_authenticated:
        return redirect('pacientes')
    return redirect('logar')


def cadastro(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            return redirect('pacientes')
        return render(request, 'cadastro.html')
    if request.method == 'POST':
        username = request.POST.get('usuario')
        senha = request.POST.get('senha')
        email = request.POST.get('email')
        confirmar_senha = request.POST.get('confirmar_senha')

        if not password_is_valid(request, senha, confirmar_senha):
            return redirect('cadastro')

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=senha,
                is_active=False,
            )
            token = sha256(f'{username}{email}'.encode()).hexdigest()
            Ativacao.objects.create(token=token, user=user)

            path_template = os.path.join(
                settings.BASE_DIR,
                'autenticacao/templates/emails/cadastro_confirmado.html',
            )
            link_ativacao = request.build_absolute_uri(
                reverse('ativar_conta', kwargs={'token': token})
            )
            email_html(
                path_template,
                'Cadastro confirmado',
                [email],
                username=username,
                link_ativacao=link_ativacao,
            )
            messages.add_message(
                request,
                constants.SUCCESS,
                'Confirme seu cadastro pelo link enviado ao e-mail.',
            )
            return redirect('logar')
        except Exception:
            messages.add_message(request, constants.ERROR, 'Erro ao cadastrar. Tente outro usuário ou e-mail.')
            return redirect('cadastro')


def logar(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            return redirect('pacientes')
        return render(request, 'logar.html')
    if request.method == "POST":
        username = request.POST.get('usuario')
        senha = request.POST.get('senha')
        usuario = auth.authenticate(username=username, password=senha)
        if not usuario:
            messages.add_message(request, constants.ERROR, 'Username ou senha inválidos')
            return redirect('logar')
        auth.login(request, usuario)
        return redirect('pacientes')


def sair(request):
    auth.logout(request)
    return redirect('logar')


def ativar_conta(request, token):
    registro = get_object_or_404(Ativacao, token=token)
    if registro.ativo:
        messages.add_message(request, constants.WARNING, 'Esse token já foi usado')
        return redirect('logar')
    user = User.objects.get(pk=registro.user_id)
    user.is_active = True
    user.save()
    registro.ativo = True
    registro.save()
    messages.add_message(request, constants.SUCCESS, 'Conta ativa com sucesso')
    return redirect('logar')
