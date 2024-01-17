from django.db import models

from authentication.models import User
from base.models import BaseModel
from instagram.models import Account


# Create your models here.
class SalesRep(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ig_username = models.CharField(max_length=255, null=True, blank=True)
    ig_password = models.CharField(max_length=255, null=True, blank=True)
    instagram = models.ManyToManyField(Account, blank=True)
    available = models.BooleanField(default=True)
    country = models.TextField(default="US")
    city = models.TextField(default="Pasadena")

    def __str__(self) -> str:
        return self.user.email
