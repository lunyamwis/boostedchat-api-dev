# Create your models here.
from django.db import models

from base.models import BaseModel


class Links(BaseModel):
    SOURCES = (
        (1, "Google"),
        (2, "StyleSeat"),
    )

    source = models.CharField(max_length=9, choices=SOURCES, default=1)
    url = models.URLField(null=True, blank=True)
