from django.db import models

from base.models import BaseModel

# Create your models here.


class Account(BaseModel):
    igname = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=255, null=True, blank=True)
    is_from_styleseat = models.BooleanField(default=False)
    review = models.FloatField(null=True, blank=True)
    gmaps_business_name = models.CharField(max_length=255, null=True, blank=True)


class HashTag(BaseModel):
    hashtag_id = models.CharField(max_length=255)


class Story(BaseModel):
    story_id = models.CharField(max_length=50, null=True, blank=True)
    link = models.URLField()


class Photo(BaseModel):
    photo_id = models.CharField(max_length=50)
    link = models.URLField()
    name = models.CharField(max_length=255)


class Video(BaseModel):
    video_id = models.CharField(max_length=50)
    link = models.URLField()
    name = models.CharField(max_length=255)


class Reel(BaseModel):
    reel_id = models.CharField(max_length=50)
    link = models.URLField()
    name = models.CharField(max_length=255)


class Comment(BaseModel):
    comment_id = models.CharField(max_length=50)
    text = models.TextField()
