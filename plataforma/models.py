from django.db import models
from django.contrib.auth.models import User


class Pacientes(models.Model):
    choices_sexo = (
        ('F', 'Feminino'),
        ('M', 'Masculino'),
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
    imagem = models.ImageField(upload_to="opcao")
    descricao = models.TextField()

    def __str__(self):
        return self.descricao
