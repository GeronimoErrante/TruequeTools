# Generated by Django 5.0.6 on 2024-06-06 21:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apptrueques', '0034_alter_venta_productos_alter_venta_publicacion'),
    ]

    operations = [
        migrations.AlterField(
            model_name='producto',
            name='cantidad_vendida',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
