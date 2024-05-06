# Generated by Django 5.0.4 on 2024-05-06 15:21

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apptrueques', '0007_categoria_alter_usuario_reputacion_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comentario',
            name='respuesta',
        ),
        migrations.AlterField(
            model_name='publicacion',
            name='categoria',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='apptrueques.categoria'),
        ),
        migrations.CreateModel(
            name='ComentarioRespuesta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('contenido', models.TextField()),
                ('fecha', models.DateField(auto_now_add=True)),
                ('comentario_original', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='respuestas', to='apptrueques.comentario')),
                ('usuario_propietario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='respuestas_publicadas', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]