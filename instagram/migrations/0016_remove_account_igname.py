# Generated by Django 4.2.4 on 2023-09-13 10:01

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("instagram", "0015_alter_thread_replied"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="account",
            name="igname",
        ),
    ]
