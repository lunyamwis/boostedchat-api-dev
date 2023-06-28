from django.db import models

from base.models import BaseModel
from scrapper.models import GmapsConfig, InstagramConfig, StyleSeatConfig


# Create your models here.
class Settings(BaseModel):
    gmaps = models.ForeignKey(GmapsConfig, on_delete=models.CASCADE, null=True, blank=True)
    styleseat = models.ForeignKey(StyleSeatConfig, on_delete=models.CASCADE, null=True, blank=True)
    instagram = models.ForeignKey(InstagramConfig, on_delete=models.CASCADE, null=True, blank=True)
