# Generated by Django 5.0.4 on 2024-05-03 02:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apptrueques', '0002_comentario_respuesta_publicacion_imagen'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='reputacion',
            field=models.IntegerField(null=True),
        ),
    ]
