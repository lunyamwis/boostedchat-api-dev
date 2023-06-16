# Generated by Django 4.2.2 on 2023-06-16 10:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("instagram", "0002_alter_account_email_alter_account_phone_number"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="story",
            name="hashtag",
        ),
        migrations.AddField(
            model_name="story",
            name="link",
            field=models.URLField(default="https://example.com"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="story",
            name="story_id",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
