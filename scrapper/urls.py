from django.urls import path

from .views import GmapScrapper

urlpatterns = [
    path("gmaps/", GmapScrapper, name="gmaps_scrapper"),
]
