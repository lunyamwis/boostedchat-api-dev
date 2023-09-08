from django.db import models

from base.models import BaseModel
from data.languages import LANGUAGES


class Industry(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name


class AutomationSheet(BaseModel):
    industry = models.ForeignKey(Industry, on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=255)
    company = models.CharField(max_length=255, null=True, blank=True)
    language = models.CharField(max_length=5, choices=LANGUAGES, default="en")
    file = models.FileField(upload_to="media")
