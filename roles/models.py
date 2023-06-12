from django.db import models
from base.models import BaseModel

# Create your models here.
class Role(BaseModel):
    name = models.CharField(max_length=255)