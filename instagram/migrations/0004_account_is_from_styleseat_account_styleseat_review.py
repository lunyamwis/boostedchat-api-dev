# Generated by Django 4.2.2 on 2023-06-23 11:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("instagram", "0003_remove_story_hashtag_story_link_story_story_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="account",
            name="is_from_styleseat",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="account",
            name="styleseat_review",
            field=models.FloatField(blank=True, null=True),
        ),
    ]
