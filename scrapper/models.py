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


class GmapsConfig(BaseModel):
    specific_element = models.CharField(max_length=255, null=True, blank=True)
    css_selector_search_box = models.CharField(max_length=255, null=True, blank=True)
    search_button = models.CharField(max_length=255, null=True, blank=True)
    delay = models.IntegerField(null=True, blank=True)
    xpath_business = models.CharField(max_length=255, null=True, blank=True)
    xpath_review = models.CharField(max_length=255, null=True, blank=True)


class StyleSeatConfig(BaseModel):
    css_selector_service_box = models.CharField(max_length=255, null=True, blank=True)
    css_selector_area_box = models.CharField(max_length=255, null=True, blank=True)
    css_selector_submit_btn = models.CharField(max_length=255, null=True, blank=True)
    css_selector_seats = models.CharField(max_length=255, null=True, blank=True)
    xpath_name = models.CharField(max_length=255, null=True, blank=True)
    xpath_popup = models.CharField(max_length=255, null=True, blank=True)
    delay = models.IntegerField(null=True, blank=True)
    xpath_ig_username = models.CharField(max_length=255, null=True, blank=True)
    xpath_review = models.CharField(max_length=255, null=True, blank=True)


class InstagramConfig(BaseModel):
    xpath_search = models.CharField(max_length=255, null=True, blank=True)
