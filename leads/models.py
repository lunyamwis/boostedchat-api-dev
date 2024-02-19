from django.db import models

# Create your models here
from base.models import BaseModel
from instagram.models import Account


# Create your models here.
class Lead(BaseModel):
    instagram = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
