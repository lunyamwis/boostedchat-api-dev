# Generated by Django 4.2.7 on 2024-08-07 07:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instagram', '0047_outreachtime'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='is_manually_triggered',
            field=models.BooleanField(default=False),
        ),
    ]
