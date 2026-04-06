from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('plataforma', '0006_pacientes_foto'),
    ]

    operations = [
        migrations.AddField(
            model_name='pacientes',
            name='peso_meta',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                max_digits=6,
                null=True,
                verbose_name='Meta de peso (kg)',
            ),
        ),
        migrations.AddField(
            model_name='pacientes',
            name='situacao',
            field=models.CharField(
                choices=[
                    ('ativo', 'Ativo'),
                    ('pausa', 'Pausado / revisão'),
                    ('alta', 'Alta'),
                ],
                default='ativo',
                max_length=20,
                verbose_name='Situação',
            ),
        ),
        migrations.CreateModel(
            name='AnotacaoPaciente',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('texto', models.TextField(max_length=2000)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('nutri', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                (
                    'paciente',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='anotacoes',
                        to='plataforma.pacientes',
                    ),
                ),
            ],
            options={
                'ordering': ['-criado_em'],
            },
        ),
    ]
