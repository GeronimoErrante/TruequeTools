# Generated by Django 5.0.4 on 2024-05-02 23:12

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Publicacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField(auto_created=True)),
                ('titulo', models.CharField(max_length=100)),
                ('descripcion', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='Sucursal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('direccion', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Solicitud',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField(auto_created=True)),
                ('publicacion_a_intercambiar', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='solicitudes_enviadas', to='apptrueques.publicacion')),
                ('publicacion_deseada', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='solicitudes_recibidas', to='apptrueques.publicacion')),
            ],
        ),
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_de_nacimiento', models.DateField(auto_created=True)),
                ('username', models.CharField(default='user_default', max_length=150, verbose_name='username', unique=False)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('password', models.CharField(max_length=50)),
                ('reputacion', models.IntegerField()),
                ('sucursal_favorita', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='usuarios', to='apptrueques.sucursal')),
            ],
        ),
        migrations.AddField(
            model_name='publicacion',
            name='usuario_propietario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='publicaciones', to='apptrueques.usuario'),
        ),
        migrations.CreateModel(
            name='Comentario',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField(auto_created=True)),
                ('contenido', models.TextField()),
                ('publicacion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comentarios', to='apptrueques.publicacion')),
                ('usuario_propietario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comentarios', to='apptrueques.usuario')),
            ],
        ),
    ]
