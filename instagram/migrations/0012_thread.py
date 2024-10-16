# Generated by Django 4.2.4 on 2023-09-07 07:46

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("instagram", "0011_remove_account_stage_statuscheck_stage"),
    ]

    operations = [
        migrations.CreateModel(
            name="Thread",
            fields=[
                (
                    "deleted_at",
                    models.DateTimeField(blank=True, db_index=True, default=None, editable=False, null=True),
                ),
                ("id", models.CharField(db_index=True, max_length=255, primary_key=True, serialize=False, unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("thread_id", models.CharField(max_length=255)),
                (
                    "account",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="instagram.account"
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
