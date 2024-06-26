# Generated by Django 5.0.4 on 2024-05-07 21:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apptrueques', '0010_alter_usuario_sucursal_favorita'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='comentariorespuesta',
            name='comentario_original',
        ),
        migrations.AddField(
            model_name='comentario',
            name='respuesta',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='comentario', to='apptrueques.comentariorespuesta'),
        ),
        migrations.AddField(
            model_name='publicacion',
            name='sucursal_destino',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='publicaciones', to='apptrueques.sucursal'),
        ),
    ]
