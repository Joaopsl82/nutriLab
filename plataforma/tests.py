from decimal import Decimal

from django.contrib.auth.models import User
from django.http import Http404
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from .models import AnotacaoPaciente, DadosPaciente, Pacientes, Refeicao
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

    def test_paciente_excluir_remove_registo(self):
        self.client.login(username='nutri1', password='Senha123')
        pk = self.paciente.pk
        url = reverse('paciente_excluir', kwargs={'id': pk})
        r = self.client.post(url)
        self.assertEqual(r.status_code, 302)
        self.assertFalse(Pacientes.objects.filter(pk=pk).exists())

    def test_paciente_excluir_outro_nutricionista_404(self):
        self.client.login(username='nutri2', password='Senha123')
        url = reverse('paciente_excluir', kwargs={'id': self.paciente.id})
        r = self.client.post(url)
        self.assertEqual(r.status_code, 404)

    def test_paciente_editar_atualiza_dados(self):
        self.client.login(username='nutri1', password='Senha123')
        url = reverse('paciente_editar', kwargs={'id': self.paciente.id})
        r = self.client.post(
            url,
            {
                'nome': 'Nome Atualizado',
                'sexo': 'F',
                'idade': '31',
                'email': 'p@test.com',
                'telefone': '11777777777',
                'situacao': 'pausa',
            },
        )
        self.assertEqual(r.status_code, 302)
        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.nome, 'Nome Atualizado')
        self.assertEqual(self.paciente.sexo, 'F')
        self.assertEqual(self.paciente.idade, 31)
        self.assertEqual(self.paciente.situacao, 'pausa')

    def test_paciente_editar_email_duplicado(self):
        Pacientes.objects.create(
            nome='Outro',
            sexo='F',
            idade=20,
            email='outro@test.com',
            telefone='11666666666',
            nutri=self.nutri,
        )
        self.client.login(username='nutri1', password='Senha123')
        url = reverse('paciente_editar', kwargs={'id': self.paciente.id})
        r = self.client.post(
            url,
            {
                'nome': self.paciente.nome,
                'sexo': 'M',
                'idade': '30',
                'email': 'outro@test.com',
                'telefone': self.paciente.telefone,
            },
        )
        self.assertEqual(r.status_code, 302)
        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.email, 'p@test.com')

    def test_pacientes_filtra_por_pesquisa(self):
        self.client.login(username='nutri1', password='Senha123')
        Pacientes.objects.create(
            nome='Outro Nome',
            sexo='F',
            idade=20,
            email='unico@test.com',
            telefone='11555555555',
            nutri=self.nutri,
        )
        r = self.client.get(reverse('pacientes'), {'q': 'unico'})
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'unico@test.com')
        self.assertNotContains(r, 'p@test.com')

    def test_export_csv_dados_clinicos(self):
        self.client.login(username='nutri1', password='Senha123')
        DadosPaciente.objects.create(
            paciente=self.paciente,
            data=timezone.now(),
            peso=Decimal('70'),
            altura=Decimal('170'),
            percentual_gordura=Decimal('10'),
            percentual_musculo=Decimal('20'),
            colesterol_hdl=Decimal('40'),
            colesterol_ldl=Decimal('50'),
            colesterol_total=Decimal('100'),
            trigliceridios=Decimal('80'),
        )
        url = reverse('dados_paciente_export_csv', kwargs={'id': self.paciente.id})
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)
        self.assertIn('text/csv', r['Content-Type'])
        body = r.content.decode('utf-8-sig')
        self.assertIn('Peso_kg', body)
        self.assertIn('70', body)

    def test_anotacao_adicionar(self):
        self.client.login(username='nutri1', password='Senha123')
        url = reverse('anotacao_adicionar', kwargs={'id': self.paciente.id})
        self.client.post(url, {'texto': '  Observação da consulta  '})
        self.assertTrue(
            AnotacaoPaciente.objects.filter(
                paciente=self.paciente,
                texto='Observação da consulta',
            ).exists()
        )

    def test_peso_meta_atualiza(self):
        self.client.login(username='nutri1', password='Senha123')
        url = reverse('paciente_peso_meta', kwargs={'id': self.paciente.id})
        self.client.post(url, {'peso_meta': '68,5'})
        self.paciente.refresh_from_db()
        self.assertEqual(self.paciente.peso_meta, Decimal('68.5'))
