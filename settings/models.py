from django.db import models

from base.models import BaseModel


class AutomationSheet(BaseModel):
    AUTOMATION_TYPES = ((1, "Stylist"),)
    category = models.IntegerField(choices=AUTOMATION_TYPES, default=1)
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to="media")
