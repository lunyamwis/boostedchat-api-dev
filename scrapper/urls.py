from django.urls import path

from .views import GmapScrapper, StyleseatScrapper

urlpatterns = [
    path("gmaps/", GmapScrapper.as_view(), name="gmaps_scrapper"),
    path("styleseat/", StyleseatScrapper.as_view(), name="styleseat_scrapper"),
]
