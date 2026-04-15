from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User


class Pacientes(models.Model):
    choices_sexo = (
        ('F', 'Feminino'),
        ('M', 'Masculino'),
    )
    choices_situacao = (
        ('ativo', 'Ativo'),
        ('pausa', 'Pausado / revisão'),
        ('alta', 'Alta'),
    )
    nome = models.CharField(max_length=50)
    foto = models.ImageField(
        upload_to='pacientes/fotos',
        blank=True,
        null=True,
        verbose_name='Foto de perfil',
    )
    sexo = models.CharField(max_length=1, choices=choices_sexo)
    idade = models.IntegerField()
    email = models.EmailField()
    telefone = models.CharField(max_length=19)
    situacao = models.CharField(
        max_length=20,
        choices=choices_situacao,
        default='ativo',
        verbose_name='Situação',
    )
    peso_meta = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Meta de peso (kg)',
    )
    nutri = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['nutri', 'email'],
                name='unique_paciente_email_por_nutri',
            ),
        ]

    def __str__(self):
        return self.nome


class AnotacaoPaciente(models.Model):
    paciente = models.ForeignKey(
        Pacientes,
        on_delete=models.CASCADE,
        related_name='anotacoes',
    )
    nutri = models.ForeignKey(User, on_delete=models.CASCADE)
    texto = models.TextField(max_length=2000)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f"Anotação {self.paciente.nome} ({self.criado_em:%Y-%m-%d})"


class FichaAnamnese(models.Model):
    paciente = models.ForeignKey(
        Pacientes,
        on_delete=models.CASCADE,
        related_name='fichas_anamnese',
    )
    nutri = models.ForeignKey(User, on_delete=models.CASCADE)
    conteudo = models.TextField(
        max_length=20000,
        verbose_name='Conteúdo da ficha',
        help_text='Queixa principal, história, hábitos, patologias, medicações, etc.',
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-atualizado_em', '-id']
        verbose_name = 'Ficha de anamnese'
        verbose_name_plural = 'Fichas de anamnese'

    def __str__(self):
        return f"Anamnese {self.paciente.nome} ({self.atualizado_em:%Y-%m-%d})"


class AvaliacaoAntropometrica(models.Model):
    paciente = models.ForeignKey(
        Pacientes,
        on_delete=models.CASCADE,
        related_name='avaliacoes_antropometricas',
    )
    nutri = models.ForeignKey(User, on_delete=models.CASCADE)
    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição',
        help_text='Motivo da consulta, observações gerais e objetivos.',
    )
    data = models.DateField(verbose_name='Data da avaliação')
    altura = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Altura (cm)',
    )
    peso_atual = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Peso atual (kg)',
    )
    peso_ideal = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Peso ideal (kg)',
    )
    # Circunferências (cm)
    braco_dir_contraido = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Braço direito contraído (cm)',
    )
    braco_esq_contraido = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Braço esquerdo contraído (cm)',
    )
    braco_dir_relaxado = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Braço direito relaxado (cm)',
    )
    braco_esq_relaxado = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Braço esquerdo relaxado (cm)',
    )
    antebraco_dir = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Antebraço direito (cm)',
    )
    antebraco_esq = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Antebraço esquerdo (cm)',
    )
    punho_dir = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Punho direito (cm)',
    )
    punho_esq = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Punho esquerdo (cm)',
    )
    tronco = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Tronco (cm)',
    )
    ombro = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Ombro (cm)',
    )
    peitoral = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Peitoral (cm)',
    )
    cintura = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Cintura (cm)',
    )
    abdomen = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Abdómen (cm)',
    )
    quadril = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Quadril (cm)',
    )
    coxa_dir = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Coxa direita (cm)',
    )
    coxa_esq = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Coxa esquerda (cm)',
    )
    panturrilha_dir = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Panturrilha direita (cm)',
    )
    panturrilha_esq = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        verbose_name='Panturrilha esquerda (cm)',
    )
    dobras_cutaneas = models.TextField(
        blank=True,
        verbose_name='Dobras / pregas cutâneas',
        help_text='Registo das dobras (mm) e fórmula utilizada, se aplicável.',
    )
    bioimpedancia = models.TextField(
        blank=True,
        verbose_name='Bioimpedância',
        help_text='Valores do equipamento, percentagens, água, etc.',
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data', '-id']
        verbose_name = 'Avaliação antropométrica'
        verbose_name_plural = 'Avaliações antropométricas'

    def __str__(self):
        return f"Antropometria {self.paciente.nome} ({self.data})"

    @property
    def imc(self):
        if self.altura and self.peso_atual and self.altura > 0:
            h_m = self.altura / Decimal('100')
            if h_m > 0:
                return self.peso_atual / (h_m * h_m)
        return None


class FotoAvaliacaoAntropometrica(models.Model):
    avaliacao = models.ForeignKey(
        AvaliacaoAntropometrica,
        on_delete=models.CASCADE,
        related_name='fotos',
    )
    imagem = models.ImageField(upload_to='avaliacoes/fotos', verbose_name='Foto')

    class Meta:
        verbose_name = 'Foto da avaliação'
        verbose_name_plural = 'Fotos da avaliação'


class AnexoExameAvaliacao(models.Model):
    avaliacao = models.ForeignKey(
        AvaliacaoAntropometrica,
        on_delete=models.CASCADE,
        related_name='anexos_exames',
    )
    arquivo = models.FileField(upload_to='avaliacoes/exames', verbose_name='Anexo (exame)')

    class Meta:
        verbose_name = 'Anexo de exame'
        verbose_name_plural = 'Anexos de exames'


class GastoEnergetico(models.Model):
    paciente = models.ForeignKey(
        Pacientes,
        on_delete=models.CASCADE,
        related_name='gastos_energeticos',
    )
    nutri = models.ForeignKey(User, on_delete=models.CASCADE)
    descricao = models.TextField(blank=True, verbose_name='Descrição / contexto')
    data = models.DateField(verbose_name='Data')
    altura = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Altura (cm)',
    )
    peso = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Peso (kg)',
    )
    calculos_protocolos = models.TextField(
        blank=True,
        verbose_name='Cálculos por protocolos',
        help_text='Ex.: Harris-Benedict, Mifflin, TEE, etc.',
    )
    nivel_atividade_met = models.TextField(
        blank=True,
        verbose_name='Nível de atividade (MET)',
        help_text='Classificação ou tabela MET utilizada.',
    )
    atividades_fisicas = models.TextField(
        blank=True,
        verbose_name='Atividades físicas',
        help_text='Tipo, duração, frequência e MET estimados.',
    )
    fator_lesao = models.DecimalField(
        max_digits=6,
        decimal_places=3,
        null=True,
        blank=True,
        verbose_name='Fator de lesão / estresse',
        help_text='Fator multiplicativo em situação de lesão, cirurgia ou inflamação.',
    )
    massa_magra_kg = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Massa magra (kg)',
    )
    resultados = models.TextField(
        blank=True,
        verbose_name='Resultados',
        help_text='GET, gasto estimado, recomendações energéticas.',
    )
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-data', '-id']
        verbose_name = 'Gasto energético'
        verbose_name_plural = 'Gastos energéticos'

    def __str__(self):
        return f"Gasto energético {self.paciente.nome} ({self.data})"


class DadosPaciente(models.Model):
    paciente = models.ForeignKey(Pacientes, on_delete=models.CASCADE)
    data = models.DateTimeField()
    peso = models.DecimalField(max_digits=6, decimal_places=2)
    altura = models.DecimalField(max_digits=5, decimal_places=2)
    percentual_gordura = models.DecimalField(max_digits=5, decimal_places=2)
    percentual_musculo = models.DecimalField(max_digits=5, decimal_places=2)
    colesterol_hdl = models.DecimalField(max_digits=6, decimal_places=2)
    colesterol_ldl = models.DecimalField(max_digits=6, decimal_places=2)
    colesterol_total = models.DecimalField(max_digits=6, decimal_places=2)
    trigliceridios = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f"Paciente({self.paciente.nome}, {self.peso})"


class Refeicao(models.Model):
    paciente = models.ForeignKey(Pacientes, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=50)
    horario = models.TimeField()
    carboidratos = models.IntegerField()
    proteinas = models.IntegerField()
    gorduras = models.IntegerField()

    def __str__(self):
        return self.titulo


class Opcao(models.Model):
    refeicao = models.ForeignKey(Refeicao, on_delete=models.CASCADE)
    titulo = models.CharField(
        max_length=120,
        blank=True,
        verbose_name='Título curto',
        help_text='Opcional. Aparece em destaque no cartão (ex.: «Sugestão de lanche»).',
    )
    imagem = models.ImageField(upload_to='opcao', blank=True, null=True, verbose_name='Imagem (opcional)')
    descricao = models.TextField(blank=True)

    def __str__(self):
        if self.titulo:
            return self.titulo
        if self.descricao:
            return self.descricao[:50]
        return f'Opção #{self.pk}'


class AlimentoNutricional(models.Model):
    """Tabela nutricional por 100 g (referência TACO / valores típicos). nutri nulo = base do sistema."""

    nutri = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='alimentos_custom',
        verbose_name='Nutricionista (vazio = base)',
    )
    nome = models.CharField(max_length=120)
    eh_prato = models.BooleanField(
        default=False,
        verbose_name='Prato / receita composta',
        help_text='Marque se for um prato com valores já agregados por 100 g.',
    )
    kcal_100g = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='Energia (kcal/100g)',
    )
    carboidratos_g_100g = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='Carboidratos (g/100g)',
    )
    proteinas_g_100g = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='Proteínas (g/100g)',
    )
    gorduras_g_100g = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='Gorduras (g/100g)',
    )
    fibra_g_100g = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='Fibra (g/100g)',
    )
    sodio_mg_100g = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='Sódio (mg/100g)',
    )
    calcio_mg_100g = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='Cálcio (mg/100g)',
    )
    ferro_mg_100g = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0,
        verbose_name='Ferro (mg/100g)',
    )

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome


class ItemRefeicaoAlimento(models.Model):
    refeicao = models.ForeignKey(
        Refeicao,
        on_delete=models.CASCADE,
        related_name='itens_alimentos',
    )
    alimento = models.ForeignKey(
        AlimentoNutricional,
        on_delete=models.CASCADE,
        related_name='usos_em_refeicoes',
    )
    quantidade_gramas = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Quantidade (g)',
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'{self.alimento.nome} ({self.quantidade_gramas} g)'
