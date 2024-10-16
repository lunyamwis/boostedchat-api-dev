# Generated by Django 4.2.4 on 2023-09-08 10:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("instagram", "0012_thread"),
    ]

    operations = [
        migrations.AddField(
            model_name="thread",
            name="replied",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="thread",
            name="replied_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
