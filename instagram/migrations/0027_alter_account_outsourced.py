# Generated by Django 4.2.4 on 2023-10-01 08:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("instagram", "0026_remove_message_robot_response_message_sent_by"),
    ]

    operations = [
        migrations.AlterField(
            model_name="account",
            name="outsourced",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to="instagram.outsourced"
            ),
        ),
    ]
