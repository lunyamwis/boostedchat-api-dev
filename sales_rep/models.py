from django.db import models
from django.utils import timezone
from authentication.models import User
from base.models import BaseModel
from instagram.models import Account
from pgcrypto import fields
import binascii


# Create your models here.
class SalesRep(BaseModel):
    STATUS_CHOICES = (
        (0,'AVAILABLE'),
        (1,'ACTIVE'),
        (2,'CHALLLENGE REQUIRED')
    )
    app_version = models.CharField(max_length=25,null=True, blank=True)
    android_version = models.IntegerField(null=True, blank=True)
    android_release = models.CharField(max_length=20,null=True, blank=True)
    dpi=models.CharField(max_length=27,null=True, blank=True)
    resolution=models.CharField(max_length=20,null=True, blank=True)
    manufacturer = models.CharField(max_length=30,null=True, blank=True)
    device = models.CharField(max_length=22,null=True, blank=True)
    model = models.CharField(max_length=22,null=True, blank=True)
    cpu = models.CharField(max_length=20,null=True, blank=True)
    version_code = models.CharField(max_length=22,null=True, blank=True)
    status = models.IntegerField(choices=STATUS_CHOICES,default=0,null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    # ig_username = models.CharField(max_length=255, null=True, blank=True)
    ig_username = fields.CharPGPSymmetricKeyField(("ig_username"),max_length=255, null=True, blank=True)
    # ig_password = models.CharField(max_length=255, null=True, blank=True)
    ig_password = fields.CharPGPSymmetricKeyField(("ig_password"),max_length=255, null=True, blank=True)  
    instagram = models.ManyToManyField(Account, blank=True)
    available = models.BooleanField(default=True)
    country = models.TextField(default="US")
    city = models.TextField(default="Pasadena")

    def __str__(self) -> str:
        return self.ig_username
    
    def get_encrypted_ig_password(self):
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT ig_password FROM sales_rep_salesrep WHERE id = %s", [self.id])
            encrypted_value = cursor.fetchone()[0]
            return binascii.hexlify(encrypted_value).decode('ascii')
    
    def get_ig_password(self) -> str:
        return self.get_encrypted_ig_password()

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