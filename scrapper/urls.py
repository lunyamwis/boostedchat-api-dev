from django.urls import path

from .views import GmapScrapper

urlpatterns = [
    path("gmaps/", GmapScrapper.as_view(), name="gmaps_scrapper"),
]
