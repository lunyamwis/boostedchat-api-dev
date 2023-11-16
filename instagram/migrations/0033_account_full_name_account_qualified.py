# Generated by Django 4.2.7 on 2023-11-15 09:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instagram', '0032_account_assigned_to'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='full_name',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
        migrations.AddField(
            model_name='account',
            name='qualified',
            field=models.BooleanField(default=False),
        ),
    ]
