# Generated manually for NutriLab improvements

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('plataforma', '0003_refeicao_opcao'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dadospaciente',
            name='peso',
            field=models.DecimalField(decimal_places=2, max_digits=6),
        ),
        migrations.AlterField(
            model_name='dadospaciente',
            name='altura',
            field=models.DecimalField(decimal_places=2, max_digits=5),
        ),
        migrations.AlterField(
            model_name='dadospaciente',
            name='percentual_gordura',
            field=models.DecimalField(decimal_places=2, max_digits=5),
        ),
        migrations.AlterField(
            model_name='dadospaciente',
            name='percentual_musculo',
            field=models.DecimalField(decimal_places=2, max_digits=5),
        ),
        migrations.AlterField(
            model_name='dadospaciente',
            name='colesterol_hdl',
            field=models.DecimalField(decimal_places=2, max_digits=6),
        ),
        migrations.AlterField(
            model_name='dadospaciente',
            name='colesterol_ldl',
            field=models.DecimalField(decimal_places=2, max_digits=6),
        ),
        migrations.AlterField(
            model_name='dadospaciente',
            name='colesterol_total',
            field=models.DecimalField(decimal_places=2, max_digits=6),
        ),
        migrations.AlterField(
            model_name='dadospaciente',
            name='trigliceridios',
            field=models.DecimalField(decimal_places=2, max_digits=6),
        ),
        migrations.AddConstraint(
            model_name='pacientes',
            constraint=models.UniqueConstraint(
                fields=('nutri', 'email'),
                name='unique_paciente_email_por_nutri',
            ),
        ),
    ]
