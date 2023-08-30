from django.db import models

from base.models import BaseModel

# Create your models here.


class ScriptStage(BaseModel):
    abbreviation = models.CharField(max_length=3)
    level = models.IntegerField()
    name = models.CharField(max_length=255)
