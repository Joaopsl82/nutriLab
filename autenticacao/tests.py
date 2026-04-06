from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import Ativacao


class AutenticacaoTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_cadastro_rejeita_nome_utilizador_com_espaco(self):
        antes = User.objects.count()
        r = self.client.post(
            reverse('cadastro'),
            {
                'primeiro_nome': 'Pedro',
                'sobrenome': 'Tolvo',
                'usuario': 'Pedro Tolvo',
                'senha': 'Abcd1234',
                'confirmar_senha': 'Abcd1234',
                'email': 'pedro@test.com',
            },
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(User.objects.count(), antes)
        msgs = [m.message for m in get_messages(r.wsgi_request)]
        self.assertTrue(any('espaços' in m.lower() for m in msgs))

    def test_cadastro_exige_sobrenome(self):
        r = self.client.post(
            reverse('cadastro'),
            {
                'primeiro_nome': 'Pedro',
                'sobrenome': '',
                'usuario': 'pedro_t',
                'senha': 'Abcd1234',
                'confirmar_senha': 'Abcd1234',
                'email': 'pedro2@test.com',
            },
        )
        self.assertEqual(r.status_code, 302)
        self.assertFalse(User.objects.filter(username='pedro_t').exists())
        msgs = [m.message for m in get_messages(r.wsgi_request)]
        self.assertTrue(any('sobrenome' in m.lower() for m in msgs))

    @override_settings(
        EMAIL_BACKEND='django.core.mail.backends.console.EmailBackend',
    )
    def test_cadastro_modo_consola_mostra_link_estruturado_no_login(self):
        r = self.client.post(
            reverse('cadastro'),
            {
                'primeiro_nome': 'Ana',
                'sobrenome': 'Silva',
                'usuario': 'nutri_dev_link',
                'senha': 'Abcd1234',
                'confirmar_senha': 'Abcd1234',
                'email': 'devlink@test.com',
            },
        )
        self.assertEqual(r.status_code, 302)
        r_login = self.client.get(r.url)
        self.assertEqual(r_login.status_code, 200)
        self.assertContains(r_login, 'Abrir link de ativação')
        self.assertContains(r_login, '/auth/ativar_conta/')

    def test_cadastro_cria_usuario_inativo_e_token(self):
        r = self.client.post(
            reverse('cadastro'),
            {
                'primeiro_nome': 'Ana',
                'sobrenome': 'Silva',
                'usuario': 'novo_nutri',
                'senha': 'Abcd1234',
                'confirmar_senha': 'Abcd1234',
                'email': 'novo@test.com',
            },
        )
        self.assertEqual(r.status_code, 302)
        user = User.objects.get(username='novo_nutri')
        self.assertEqual(user.first_name, 'Ana')
        self.assertEqual(user.last_name, 'Silva')
        self.assertFalse(user.is_active)
        self.assertTrue(Ativacao.objects.filter(user=user).exists())
        reg = Ativacao.objects.get(user=user)
        self.assertIsInstance(reg.token, str)
        self.assertGreater(len(reg.token), 32)

    def test_ativar_conta_ativa_usuario(self):
        user = User.objects.create_user(
            username='u',
            password='Abcd1234',
            email='u@test.com',
            is_active=False,
        )
        reg = Ativacao.objects.create(token='tokentest123456789012345678901234567890', user=user)
        url = reverse('ativar_conta', kwargs={'token': reg.token})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        reg.refresh_from_db()
        self.assertTrue(reg.ativo)

    def test_logar_utilizador_ativo_redireciona(self):
        User.objects.create_user(
            username='nutri_ok',
            password='Abcd1234',
            email='ok@test.com',
            is_active=True,
        )
        r = self.client.post(
            reverse('logar'),
            {'username': 'nutri_ok', 'password': 'Abcd1234'},
            follow=False,
        )
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.url, '/pacientes/')

    def test_navbar_mostra_nome_completo_quando_existir(self):
        User.objects.create_user(
            username='nutri_nome',
            password='Abcd1234',
            email='n@test.com',
            first_name='Pedro',
            last_name='Tolvo',
            is_active=True,
        )
        self.client.login(username='nutri_nome', password='Abcd1234')
        r = self.client.get(reverse('pacientes'))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'Bem-vindo')
        self.assertContains(r, 'Pedro Tolvo')
