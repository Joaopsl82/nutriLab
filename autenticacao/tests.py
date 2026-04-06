from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from .models import Ativacao


class AutenticacaoTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_cadastro_cria_usuario_inativo_e_token(self):
        r = self.client.post(
            reverse('cadastro'),
            {
                'usuario': 'novo_nutri',
                'senha': 'Abcd1234',
                'confirmar_senha': 'Abcd1234',
                'email': 'novo@test.com',
            },
        )
        self.assertEqual(r.status_code, 302)
        user = User.objects.get(username='novo_nutri')
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
