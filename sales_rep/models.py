from django.db import models

from authentication.models import User
from base.models import BaseModel


# Create your models here.
class SalesRep(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
