# Generated by Django 4.2.7 on 2024-02-15 12:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instagram', '0040_remove_account_qualified_keywords'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='referral',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='account',
            name='status_param',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
