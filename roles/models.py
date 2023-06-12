from django.db import models
from base.models import BaseModel # should be available

# Create your models here.
class Role(BaseModel):
    name = models.CharField(max_length=255)