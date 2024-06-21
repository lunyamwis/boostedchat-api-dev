from django.db import models
from django.utils import timezone
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


class Influencer(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    ig_username = models.CharField(max_length=255, null=True, blank=True)
    ig_password = models.CharField(max_length=255, null=True, blank=True)
    instagram = models.ManyToManyField(Account, blank=True)
    available = models.BooleanField(default=True)
    country = models.TextField(default="US")
    city = models.TextField(default="Pasadena")

    def __str__(self) -> str:
        return self.user.email

class LeadAssignmentHistory(models.Model):
    influencer = models.ForeignKey(Influencer, on_delete=models.CASCADE,null=True,blank=True)
    sales_rep = models.ForeignKey(SalesRep, on_delete=models.CASCADE,null=True,blank=True)
    lead = models.ForeignKey(Account, on_delete=models.CASCADE)
    assigned_at = models.DateTimeField(default=timezone.now)

    def __str__(self) -> str:
        return self.sales_rep.ig_username +"=====>"+self.lead.igname