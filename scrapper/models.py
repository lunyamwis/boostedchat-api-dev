# Create your models here.
from django.db import models

from base.models import BaseModel


class Links(BaseModel):
    url = models.URLField(null=True, blank=True)
