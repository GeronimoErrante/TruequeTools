# Generated by Django 5.0.6 on 2024-05-22 17:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apptrueques', '0015_empleado'),
    ]

    operations = [
        migrations.AddField(
            model_name='empleado',
            name='is_staff',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='empleado',
            name='password',
            field=models.CharField(default='password', max_length=128),
        ),
    ]
