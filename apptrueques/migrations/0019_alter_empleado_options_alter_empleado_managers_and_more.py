# Generated by Django 5.0.6 on 2024-05-22 19:02

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apptrueques', '0018_alter_empleado_is_staff_alter_empleado_password'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='empleado',
            options={},
        ),
        migrations.AlterModelManagers(
            name='empleado',
            managers=[
            ],
        ),
        migrations.RemoveField(
            model_name='empleado',
            name='date_joined',
        ),
        migrations.RemoveField(
            model_name='empleado',
            name='email',
        ),
        migrations.RemoveField(
            model_name='empleado',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='empleado',
            name='groups',
        ),
        migrations.RemoveField(
            model_name='empleado',
            name='is_active',
        ),
        migrations.RemoveField(
            model_name='empleado',
            name='is_staff',
        ),
        migrations.RemoveField(
            model_name='empleado',
            name='is_superuser',
        ),
        migrations.RemoveField(
            model_name='empleado',
            name='last_login',
        ),
        migrations.RemoveField(
            model_name='empleado',
            name='last_name',
        ),
        migrations.RemoveField(
            model_name='empleado',
            name='nombre',
        ),
        migrations.RemoveField(
            model_name='empleado',
            name='password',
        ),
        migrations.RemoveField(
            model_name='empleado',
            name='user_permissions',
        ),
        migrations.RemoveField(
            model_name='empleado',
            name='username',
        ),
        migrations.AddField(
            model_name='empleado',
            name='user',
            field=models.OneToOneField(default='', on_delete=django.db.models.deletion.CASCADE, parent_link=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='empleado',
            name='dni',
            field=models.CharField(default='', max_length=11, unique=True),
        ),
    ]