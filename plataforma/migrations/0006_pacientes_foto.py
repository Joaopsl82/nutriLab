from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plataforma', '0005_alter_pacientes_sexo'),
    ]

    operations = [
        migrations.AddField(
            model_name='pacientes',
            name='foto',
            field=models.ImageField(
                blank=True,
                null=True,
                upload_to='pacientes/fotos',
                verbose_name='Foto de perfil',
            ),
        ),
    ]
