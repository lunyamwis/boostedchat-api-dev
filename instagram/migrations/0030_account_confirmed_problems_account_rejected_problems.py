# Generated by Django 4.2.4 on 2023-10-02 10:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("instagram", "0029_merge_20231001_1026"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="confirmed_problems",
            field=models.TextField(blank=True, default="test", null=True),
        ),
        migrations.AddField(
            model_name="account",
            name="rejected_problems",
            field=models.TextField(blank=True, default="test", null=True),
        ),
    ]
