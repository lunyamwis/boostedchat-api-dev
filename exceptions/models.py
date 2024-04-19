from django.db import models
from instagram.models import Account

# Create your models here.
class ExceptionModel(models.Model):
    CODES = (
        (401,401),
        (403,403)
    )
    code = models.IntegerField(choices=CODES)
    timestamp = models.DateTimeField(auto_now_add=True)
    affected_account = models.ForeignKey(Account,on_delete=models.CASCADE, null=True, blank=True)
    data = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)


    