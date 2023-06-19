from django.urls import include, path
from helpers.setup import Setup
from rest_framework.test import APITestCase, URLPatternsTestCase


class UserTest(APITestCase, URLPatternsTestCase):
    """Test module for User"""

    urlpatterns = [
        path("api/v1/scrapper/", include("scrapper.urls")),
    ]

    def setup(self):
        self.soup, self.driver = Setup("gmaps").derive_gmap_config()
