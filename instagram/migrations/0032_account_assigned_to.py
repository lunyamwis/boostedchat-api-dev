# Generated by Django 4.2.5 on 2023-10-19 06:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instagram', '0031_alter_account_igname'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='assigned_to',
            field=models.TextField(default='Robot'),
        ),
    ]
