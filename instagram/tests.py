# Create your tests here.

from django.urls import include, path, reverse
from rest_framework import status
from rest_framework.test import APITestCase, URLPatternsTestCase

from .models import Account, Comment, HashTag, Photo, Reel, Story, Video


class UserTest(APITestCase, URLPatternsTestCase):
    """Test module for User"""

    urlpatterns = [
        path("api/v1/instagram/", include("instagram.urls")),
    ]

    def setUp(self):
        self.account = Account.objects.create(igname="Vmbeautydallas")

        self.story = Story.objects.create(link="admin@test.com")

        self.comment = Comment.objects.create(comment_id="admin@test.com")

        self.hashtag = HashTag.objects.create(hashtag_id="test_id")

        self.photo = Photo.objects.create(link="https://www.instagram.com/p/Ctc5sY9xqCl/")

        self.reel = Reel.objects.create(link="https://www.instagram.com/reels/Cqb6IjJu18m/")

        self.video = Video.objects.create(link="https://www.instagram.com/p/ChAsEdoJfOt/")

    def test_null_values_in_extract_action_button(self):
        url = reverse("account-extract_action_button")
        response = self.client.get(url)
        nones = not all(response.data.values())
        self.assertFalse(nones)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
