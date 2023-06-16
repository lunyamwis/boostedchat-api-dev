# Create your views here.
import os

from instagrapi import Client
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Account, Comment, HashTag, Photo, Reel, Story, Video
from .serializers import (
    AccountSerializer,
    CommentSerializer,
    HashTagSerializer,
    PhotoSerializer,
    ReelSerializer,
    StorySerializer,
    VideoSerializer,
)


class AccountViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    @action(detail=True, methods=["get"], url_path="extract-followers")
    def extract_followers(self, request, pk=None):
        account = self.get_object()
        cl = Client()
        cl.login(os.getenv("IG_USERNAME"), os.getenv("IG_PASSWORD"))
        user_info = cl.user_info_by_username(account.igname).dict()
        followers = cl.user_followers(user_info["pk"])
        return Response(followers)


class HashTagViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    queryset = HashTag.objects.all()
    serializer_class = HashTagSerializer


class PhotoViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer

    @action(detail=True, methods=["get"], url_path="retrieve-likers")
    def retrieve_likers(self, request, pk=None):
        photo = self.get_object()
        cl = Client()
        cl.login(os.getenv("IG_USERNAME"), os.getenv("IG_PASSWORD"))
        media_pk = cl.media_pk_from_url(photo.link)
        likers = cl.media_likers(media_pk)
        return Response(likers)


class VideoViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    queryset = Video.objects.all()
    serializer_class = VideoSerializer

    @action(detail=True, methods=["get"], url_path="retrieve-likers")
    def retrieve_likers(self, request, pk=None):
        video = self.get_object()
        cl = Client()
        cl.login(os.getenv("IG_USERNAME"), os.getenv("IG_PASSWORD"))
        media_pk = cl.media_pk_from_url(video.link)
        likers = cl.media_likers(media_pk)
        return Response(likers)


class ReelViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    queryset = Reel.objects.all()
    serializer_class = ReelSerializer

    @action(detail=True, methods=["get"], url_path="retrieve-likers")
    def retrieve_likers(self, request, pk=None):
        reel = self.get_object()
        cl = Client()
        cl.login(os.getenv("IG_USERNAME"), os.getenv("IG_PASSWORD"))
        media_pk = cl.media_pk_from_url(reel.link)
        likers = cl.media_likers(media_pk)
        return Response(likers)


class CommentViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    queryset = Comment.objects.all()
    serializer_class = CommentSerializer


class StoryViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    queryset = Story.objects.all()
    serializer_class = StorySerializer

    @action(detail=True, methods=["get"], url_path="retrieve-viewers")
    def retrieve_viewers(self, request, pk=None):
        photo = self.get_object()
        cl = Client()
        cl.login(os.getenv("IG_USERNAME"), os.getenv("IG_PASSWORD"))
        media_pk = cl.story_pk_from_url(photo.link)
        likers = cl.story_viewers(media_pk)
        return Response(likers)
