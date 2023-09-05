# Generated by Django 4.2.4 on 2023-09-05 08:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("instagram", "0008_photo_account"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="stage",
            field=models.IntegerField(
                choices=[(1, "Oven"), (2, "Needs Assessment"), (3, "Overcoming Objections"), (4, "Activation")],
                default=1,
            ),
        ),
    ]
