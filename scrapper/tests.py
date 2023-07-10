from django.urls import include, path, reverse
from rest_framework.test import APITestCase, URLPatternsTestCase

from .helpers.setup import Setup


class UserTest(APITestCase, URLPatternsTestCase):
    """Test module for User"""

    urlpatterns = [
        path("api/v1/scrapper/", include("scrapper.urls")),
    ]

    def setup(self):
        self.soup, self.driver = Setup("gmaps").derive_gmap_config()

    def test_extract_similar_accounts(self):
        url = reverse("extract_similar_accounts")
        print(url)
        # response = self.client.get(url)
