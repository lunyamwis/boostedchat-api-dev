# Generated by Django 4.2.4 on 2023-09-04 07:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("instagram", "0007_remove_account_photo_remove_account_reel_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="photo",
            name="account",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="instagram.account"
            ),
        ),
    ]
