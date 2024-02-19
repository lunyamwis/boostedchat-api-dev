# Generated by Django 4.2.4 on 2023-11-17 10:43

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("instagram", "0033_account_full_name_account_qualified"),
    ]

    operations = [
        migrations.AddField(
            model_name="outsourced",
            name="created_at",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="outsourced",
            name="deleted_at",
            field=models.DateTimeField(blank=True, db_index=True, default=None, editable=False, null=True),
        ),
        migrations.AddField(
            model_name="outsourced",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="outsourced",
            name="id",
            field=models.CharField(db_index=True, max_length=255, primary_key=True, serialize=False, unique=True),
        ),
    ]
