# Generated by Django 4.2.4 on 2023-09-13 10:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("instagram", "0016_remove_account_igname"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="igname",
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
    ]
