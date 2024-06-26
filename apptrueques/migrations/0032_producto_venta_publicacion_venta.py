# Generated by Django 5.0.6 on 2024-06-05 16:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apptrueques', '0031_remove_empleado_nombre_alter_empleado_username'),
    ]

    operations = [
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=50)),
                ('precio_unitario', models.FloatField()),
                ('cantidad_vendida', models.FloatField()),
            ],
        ),
        migrations.CreateModel(
            name='Venta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('productos', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='productos_vendidos', to='apptrueques.producto')),
            ],
        ),
        migrations.AddField(
            model_name='publicacion',
            name='venta',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='apptrueques.venta'),
        ),
    ]
