import os
from hashlib import sha256

from django.conf import settings
from django.contrib import auth
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.auth.views import LoginView
from django.contrib.messages import constants
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie

from .forms import NutriAuthenticationForm
from .models import Ativacao
from .utils import email_html, password_is_valid


def home(request):
    if request.user.is_authenticated:
        return redirect('pacientes')
    return redirect('logar')


SESSION_ACTIVATION_URL = 'pending_activation_url'


@method_decorator(ensure_csrf_cookie, name='dispatch')
class NutriLoginView(LoginView):
    template_name = 'logar.html'
    authentication_form = NutriAuthenticationForm
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activation_url'] = self.request.session.pop(SESSION_ACTIVATION_URL, None)
        return context


@ensure_csrf_cookie
def cadastro(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            return redirect('pacientes')
        return render(request, 'cadastro.html')
    if request.method == 'POST':
        primeiro_nome = (request.POST.get('primeiro_nome') or '').strip()
        sobrenome = (request.POST.get('sobrenome') or '').strip()
        username = (request.POST.get('usuario') or '').strip()
        senha = request.POST.get('senha')
        email = (request.POST.get('email') or '').strip()
        confirmar_senha = request.POST.get('confirmar_senha')

        if not primeiro_nome:
            messages.add_message(
                request,
                constants.ERROR,
                'Indique o seu nome.',
            )
            return redirect('cadastro')

        if not sobrenome:
            messages.add_message(
                request,
                constants.ERROR,
                'Indique o seu sobrenome.',
            )
            return redirect('cadastro')

        if not username:
            messages.add_message(
                request,
                constants.ERROR,
                'Indique um nome de utilizador.',
            )
            return redirect('cadastro')

        if any(c.isspace() for c in username):
            messages.add_message(
                request,
                constants.ERROR,
                'O nome de utilizador não pode ter espaços. Para «Utilizador», use por exemplo «utilizador.exemplo» ou «utilizador_exemplo».',
            )
            return redirect('cadastro')

        try:
            UnicodeUsernameValidator()(username)
        except ValidationError:
            messages.add_message(
                request,
                constants.ERROR,
                'Nome de utilizador inválido: use apenas letras, números e os símbolos @ . + - _ (sem espaços).',
            )
            return redirect('cadastro')

        if not password_is_valid(request, senha, confirmar_senha):
            return redirect('cadastro')

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=senha,
                first_name=primeiro_nome[:150],
                last_name=sobrenome[:150],
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
                'Confirme o seu registo — NutriPraxis',
                [email],
                username=username,
                link_ativacao=link_ativacao,
            )
            if settings.EMAIL_BACKEND.endswith('console.EmailBackend'):
                request.session[SESSION_ACTIVATION_URL] = link_ativacao
                messages.add_message(
                    request,
                    constants.SUCCESS,
                    'Conta criada. Por favor, confirme o registo abrindo o link abaixo.',
                )
            else:
                messages.add_message(
                    request,
                    constants.SUCCESS,
                    'Confirme o registo abrindo o link que enviámos para o seu e-mail.',
                )
            return redirect('logar')
        except Exception:
            messages.add_message(request, constants.ERROR, 'Erro ao cadastrar. Tente outro usuário ou e-mail.')
            return redirect('cadastro')


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
