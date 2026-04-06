from decimal import Decimal

from django.contrib.auth.models import User
from django.http import Http404
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from .models import DadosPaciente, Pacientes, Refeicao
from .views import grafico_peso, opcao


class PlataformaViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.nutri = User.objects.create_user(
            username='nutri1',
            password='Senha123',
            email='n1@test.com',
        )
        self.outro = User.objects.create_user(
            username='nutri2',
            password='Senha123',
            email='n2@test.com',
        )
        self.paciente = Pacientes.objects.create(
            nome='Paciente A',
            sexo='M',
            idade=30,
            email='p@test.com',
            telefone='11999999999',
            nutri=self.nutri,
        )

    def test_grafico_peso_get_somente_dono(self):
        self.client.login(username='nutri1', password='Senha123')
        url = reverse('grafico_peso', kwargs={'id': self.paciente.id})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn('peso', data)
        self.assertIn('labels', data)

    def test_grafico_peso_post_nao_permitido(self):
        self.client.login(username='nutri1', password='Senha123')
        url = reverse('grafico_peso', kwargs={'id': self.paciente.id})
        r = self.client.post(url)
        self.assertEqual(r.status_code, 405)

    def test_grafico_peso_outro_nutricionista_404(self):
        rf = RequestFactory()
        url = reverse('grafico_peso', kwargs={'id': self.paciente.id})
        req = rf.get(url)
        req.user = self.outro
        with self.assertRaises(Http404):
            grafico_peso(req, id=str(self.paciente.id))

    def test_grafico_peso_exige_login(self):
        url = reverse('grafico_peso', kwargs={'id': self.paciente.id})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 302)

    def test_dados_paciente_post_invalido_nao_grava(self):
        self.client.login(username='nutri1', password='Senha123')
        url = reverse('dados_paciente', kwargs={'id': self.paciente.id})
        antes = DadosPaciente.objects.filter(paciente=self.paciente).count()
        self.client.post(
            url,
            {
                'peso': 'abc',
                'altura': '170',
                'gordura': '10',
                'musculo': '20',
                'hdl': '40',
                'ldl': '50',
                'ctotal': '100',
                'triglicerídios': '80',
            },
        )
        depois = DadosPaciente.objects.filter(paciente=self.paciente).count()
        self.assertEqual(antes, depois)

    def test_dados_paciente_post_valido_grava(self):
        self.client.login(username='nutri1', password='Senha123')
        url = reverse('dados_paciente', kwargs={'id': self.paciente.id})
        self.client.post(
            url,
            {
                'peso': '70',
                'altura': '170',
                'gordura': '10',
                'musculo': '20',
                'hdl': '40',
                'ldl': '50',
                'ctotal': '100',
                'triglicerídios': '80',
            },
        )
        self.assertTrue(
            DadosPaciente.objects.filter(
                paciente=self.paciente,
                peso=Decimal('70'),
            ).exists()
        )

    def test_plano_alimentar_listar_exige_login(self):
        r = self.client.get(reverse('plano_alimentar_listar'))
        self.assertEqual(r.status_code, 302)

    def test_opcao_refeicao_de_outro_paciente_404(self):
        outro_p = Pacientes.objects.create(
            nome='B',
            sexo='F',
            idade=25,
            email='b@test.com',
            telefone='11888888888',
            nutri=self.outro,
        )
        ref = Refeicao.objects.create(
            paciente=outro_p,
            titulo='Cafe',
            horario='08:00',
            carboidratos=10,
            proteinas=10,
            gorduras=5,
        )
        rf = RequestFactory()
        url = reverse('opcao', kwargs={'id_paciente': self.paciente.id})
        req = rf.post(url, {'refeicao': str(ref.id), 'descricao': 'x'})
        req.user = self.nutri
        with self.assertRaises(Http404):
            opcao(req, id_paciente=str(self.paciente.id))
