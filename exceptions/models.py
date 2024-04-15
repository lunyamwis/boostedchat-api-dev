from django.db import models

# Create your models here.
class ExceptionModel(models.Model):
    CODES = (
        (401,401),
        (403,403)
    )
    code = models.IntegerField(choices=CODES)