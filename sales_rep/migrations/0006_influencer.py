# Generated by Django 5.0.6 on 2024-06-21 13:12

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('instagram', '0043_account_script_score_account_script_version'),
        ('sales_rep', '0005_leadassignmenthistory'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Influencer',
            fields=[
                ('deleted_at', models.DateTimeField(blank=True, db_index=True, default=None, editable=False, null=True)),
                ('id', models.CharField(db_index=True, max_length=255, primary_key=True, serialize=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('ig_username', models.CharField(blank=True, max_length=255, null=True)),
                ('ig_password', models.CharField(blank=True, max_length=255, null=True)),
                ('available', models.BooleanField(default=True)),
                ('country', models.TextField(default='US')),
                ('city', models.TextField(default='Pasadena')),
                ('instagram', models.ManyToManyField(blank=True, to='instagram.account')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
