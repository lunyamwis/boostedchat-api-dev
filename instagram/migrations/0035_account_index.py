# Generated by Django 4.2.7 on 2023-11-28 15:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instagram', '0034_outsourced_created_at_outsourced_deleted_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='index',
            field=models.IntegerField(default=0),
        ),
    ]
