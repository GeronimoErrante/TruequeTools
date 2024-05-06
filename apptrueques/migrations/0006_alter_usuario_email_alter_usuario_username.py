# Generated by Django 5.0.4 on 2024-05-04 00:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apptrueques', '0005_alter_usuario_options_alter_usuario_managers_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='email',
            field=models.EmailField(max_length=254, unique=True),
        ),
        migrations.AlterField(
            model_name='usuario',
            name='username',
            field=models.CharField(max_length=150),
        ),
    ]