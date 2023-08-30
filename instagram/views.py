# Create your views here.
import csv
import io
import logging
import uuid
from urllib.parse import urlparse

from instagrapi.exceptions import UserNotFound
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from base.helpers.push_id import PushID
from dialogflow.helpers.intents import detect_intent
from instagram.helpers.login import login_user

from .models import Account, Comment, HashTag, Photo, Reel, Story, Video
from .serializers import (
    AccountSerializer,
    AddCommentSerializer,
    CommentSerializer,
    HashTagSerializer,
    PhotoSerializer,
    ReelSerializer,
    StorySerializer,
    UploadSerializer,
    VideoSerializer,
)


class AccountViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    queryset = Account.objects.all()
    serializer_class = AccountSerializer

    def get_serializer_class(self):
        if self.action == "batch_uploads":
            return UploadSerializer
        return self.serializer_class

    @action(detail=True, methods=["get"], url_path="potential-buy")
    def potential_buy(self, request, pk=None):
        account = self.get_object()
        status_code = 0
        cl = login_user()

        user_info = cl.user_info_by_username(account.igname).dict()
        potential_buy = 0
        l1 = ["hello", "hi"]
        l2 = user_info["biography"].split(" ")
        for i in l1:
            if l2.count(i) > 0:
                potential_buy = 50
                break
            status_code = 200

        return Response({"status_code": status_code, "potential_buy": potential_buy})

    @action(detail=True, methods=["get"], url_path="potential-promote")
    def potential_promote(self, request, pk=None):
        account = self.get_object()
        status_code = 0
        cl = login_user()

        user_info = cl.user_info_by_username(account.igname).dict()
        l1 = ["hello", "hi"]
        l2 = user_info["biography"].split(" ")
        potential_promote = 0
        for i in l1:
            if l2.count(i) > 0:
                potential_promote = 50
                break
            status_code = 200

        return Response({"status_code": status_code, "potential_promote": potential_promote})

    @action(detail=True, methods=["get"], url_path="extract-followers")
    def extract_followers(self, request, pk=None):
        account = self.get_object()
        cl = login_user()

        user_info = cl.user_info_by_username(account.igname).dict()
        followers = cl.user_followers(user_info["pk"])
        for follower in followers:
            account_ = Account()
            account_.igname = followers[follower].username
            account_.save()
        return Response(followers)

    @action(detail=False, methods=["post"], url_path="batch-uploads")
    def batch_uploads(self, request):
        serializer = UploadSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)

        if valid:
            paramFile = io.TextIOWrapper(request.FILES["file_uploaded"].file)
            portfolio1 = csv.DictReader(paramFile)
            list_of_dict = list(portfolio1)
            objs = [Account(id=PushID().next_id(), igname=row["username"]) for row in list_of_dict]
            try:
                msg = Account.objects.bulk_create(objs)
                returnmsg = {"status_code": 200}
                print(f"imported {msg} successfully")
            except Exception as e:
                print("Error While Importing Data: ", e)
                returnmsg = {"status_code": 500}

            return Response(returnmsg)

        else:
            return Response({"status_code": 500})

    @action(detail=False, methods=["get"], url_path="extract-action-button", url_name="extract_action_button")
    def extract_action_bution(self, request):
        status_code = 0
        external_urls = []
        cl = login_user()

        for _, account in enumerate(self.queryset):
            try:
                url_info = cl.user_info_by_username(account.igname)
            except UserNotFound as err:
                logging.warning(err)

            account.competitor = urlparse(url_info.external_url).netloc
            account.save()
            external_url_info = {
                "external_url": url_info.external_url,
                "category": url_info.category,
                "competitor": account.competitor,
            }
            external_urls.append(external_url_info)
            status_code = status.HTTP_200_OK
            logging.warning(f"extracting info from => {account.igname}")

        response = {"actions": external_urls, "status_code": status_code}
        return Response(response)


class HashTagViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    queryset = HashTag.objects.all()
    serializer_class = HashTagSerializer

    def get_serializer_class(self):
        if self.action == "batch_uploads":
            return UploadSerializer
        return self.serializer_class

    @action(detail=False, methods=["post"], url_path="batch-uploads")
    def batch_uploads(self, request):
        serializer = UploadSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)

        if valid:
            paramFile = io.TextIOWrapper(request.FILES["file_uploaded"].file)
            portfolio1 = csv.DictReader(paramFile)
            list_of_dict = list(portfolio1)
            objs = [HashTag(id=PushID().next_id(), name=row["name"]) for row in list_of_dict]
            try:
                msg = HashTag.objects.bulk_create(objs)
                returnmsg = {"status_code": 200}
                print(f"imported {msg} successfully")
            except Exception as e:
                print("Error While Importing Data: ", e)
                returnmsg = {"status_code": 500}

            return Response(returnmsg)

        else:
            return Response({"status_code": 500})


class PhotoViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer

    def get_serializer_class(self):
        if self.action == "batch_uploads":
            return UploadSerializer
        elif self.action == "add_comment":
            return AddCommentSerializer
        return self.serializer_class

    @action(detail=True, methods=["get"], url_path="retrieve-likers")
    def retrieve_likers(self, request, pk=None):
        photo = self.get_object()
        cl = login_user()

        media_pk = cl.media_pk_from_url(photo.link)
        likers = cl.media_likers(media_pk)
        for liker in likers:
            account = Account()
            account.igname = liker.username
            account.save()
        return Response(likers)

    @action(detail=True, methods=["get"], url_path="fetch-comments")
    def fetch_comments(self, request, pk=None):
        try:
            photo = self.get_object()
            cl = login_user()
            media_pk = cl.media_pk_from_url(photo.link)
            media_id = cl.media_id(media_pk=media_pk)
            comments = cl.media_comments(media_id=media_id)
            response = {"comments": comments, "length": len(comments)}
            return Response(response, status=status.HTTP_200_OK)
        except Exception as error:
            error_message = str(error)
            return Response({"error": error_message})

    @action(detail=True, methods=["post"], url_path="add-comment")
    def add_comment(self, request, pk=None):
        photo = self.get_object()
        cl = login_user()

        media_pk = cl.media_pk_from_url(photo.link)
        media_id = cl.media_id(media_pk=media_pk)
        serializer = AddCommentSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)
        generated_response = detect_intent(
            project_id="boostedchatapi",
            session_id=str(uuid.uuid4()),
            message=serializer.data.get("text"),
            language_code="en",
        )
        if valid:
            cl.media_comment(media_id, generated_response)

        return Response({"status": status.HTTP_200_OK, "message": generated_response, "success": True})

    @action(detail=True, methods=["get"], url_path="retrieve-commenters")
    def retrieve_commenters(self, request, pk=None):
        photo = self.get_object()
        cl = login_user()

        media_pk = cl.media_pk_from_url(photo.link)
        comments = cl.media_comments(media_pk)
        for comment in comments:
            account = Account()
            account.igname = comment.user.username
            account.save()
        return Response(comments)

    @action(detail=False, methods=["post"], url_path="batch-uploads")
    def batch_uploads(self, request):
        serializer = UploadSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)

        if valid:
            paramFile = io.TextIOWrapper(request.FILES["file_uploaded"].file)
            portfolio1 = csv.DictReader(paramFile)
            list_of_dict = list(portfolio1)
            objs = [Photo(id=PushID().next_id(), link=row["link"]) for row in list_of_dict]
            try:
                msg = Photo.objects.bulk_create(objs)
                returnmsg = {"status_code": 200}
                print(f"imported {msg} successfully")
            except Exception as e:
                print("Error While Importing Data: ", e)
                returnmsg = {"status_code": 500}

            return Response(returnmsg)

        else:
            return Response({"status_code": 500})


class VideoViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    queryset = Video.objects.all()
    serializer_class = VideoSerializer

    def get_serializer_class(self):
        if self.action == "batch_uploads":
            return UploadSerializer
        elif self.action == "add_comment":
            return AddCommentSerializer
        return self.serializer_class

    @action(detail=True, methods=["get"], url_path="fetch-comments")
    def fetch_comments(self, request, pk=None):
        try:
            video = self.get_object()
            cl = login_user()
            media_pk = cl.media_pk_from_url(video.link)
            media_id = cl.media_id(media_pk=media_pk)
            comments = cl.media_comments(media_id=media_id)
            response = {"comments": comments, "length": len(comments)}
            return Response(response, status=status.HTTP_200_OK)
        except Exception as error:
            error_message = str(error)
            return Response({"error": error_message})

    @action(detail=True, methods=["post"], url_path="add-comment")
    def add_comment(self, request, pk=None):
        video = self.get_object()
        cl = login_user()

        media_pk = cl.media_pk_from_url(video.link)
        media_id = cl.media_id(media_pk=media_pk)
        serializer = AddCommentSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)
        generated_response = detect_intent(
            project_id="boostedchatapi",
            session_id=str(uuid.uuid4()),
            message=serializer.data.get("text"),
            language_code="en",
        )
        if valid:
            cl.media_comment(media_id, generated_response)

        return Response({"status": status.HTTP_200_OK, "message": generated_response, "success": True})

    @action(detail=True, methods=["get"], url_path="retrieve-likers")
    def retrieve_likers(self, request, pk=None):
        video = self.get_object()
        cl = login_user()

        media_pk = cl.media_pk_from_url(video.link)
        likers = cl.media_likers(media_pk)
        for liker in likers:
            account = Account()
            account.igname = liker.username
            account.save()
        return Response(likers)

    @action(detail=True, methods=["get"], url_path="retrieve-commenters")
    def retrieve_commenters(self, request, pk=None):
        video = self.get_object()
        cl = login_user()

        media_pk = cl.media_pk_from_url(video.link)
        comments = cl.media_comments(media_pk)
        for comment in comments:
            account = Account()
            account.igname = comment.user.username
            account.save()
        return Response(comments)

    @action(detail=False, methods=["post"], url_path="batch-uploads")
    def batch_uploads(self, request):
        serializer = UploadSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)

        if valid:
            paramFile = io.TextIOWrapper(request.FILES["file_uploaded"].file)
            portfolio1 = csv.DictReader(paramFile)
            list_of_dict = list(portfolio1)
            objs = [Video(id=PushID().next_id(), link=row["link"]) for row in list_of_dict]
            try:
                msg = Video.objects.bulk_create(objs)
                returnmsg = {"status_code": 200}
                print(f"imported {msg} successfully")
            except Exception as e:
                print("Error While Importing Data: ", e)
                returnmsg = {"status_code": 500}

            return Response(returnmsg)

        else:
            return Response({"status_code": 500})


class ReelViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    queryset = Reel.objects.all()
    serializer_class = ReelSerializer

    def get_serializer_class(self):
        if self.action == "batch_uploads":
            return UploadSerializer
        elif self.action == "add_comment":
            return AddCommentSerializer

        return self.serializer_class

    @action(detail=True, methods=["get"], url_path="fetch-comments")
    def fetch_comments(self, request, pk=None):
        try:
            reel = self.get_object()
            cl = login_user()
            media_pk = cl.media_pk_from_url(reel.link)
            media_id = cl.media_id(media_pk=media_pk)
            comments = cl.media_comments(media_id=media_id)
            response = {"comments": comments, "length": len(comments)}
            return Response(response, status=status.HTTP_200_OK)
        except Exception as error:
            error_message = str(error)
            return Response({"error": error_message})

    @action(detail=True, methods=["post"], url_path="add-comment")
    def add_comment(self, request, pk=None):
        reel = self.get_object()
        cl = login_user()

        media_pk = cl.media_pk_from_url(reel.link)
        media_id = cl.media_id(media_pk=media_pk)
        serializer = AddCommentSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)
        generated_response = detect_intent(
            project_id="boostedchatapi",
            session_id=str(uuid.uuid4()),
            message=serializer.data.get("text"),
            language_code="en",
        )
        if valid:
            cl.media_comment(media_id, generated_response)

        return Response({"status": status.HTTP_200_OK, "message": generated_response, "success": True})

    @action(detail=True, methods=["get"], url_path="retrieve-likers")
    def retrieve_likers(self, request, pk=None):
        reel = self.get_object()
        cl = login_user()

        media_pk = cl.media_pk_from_url(reel.link)
        likers = cl.media_likers(media_pk)
        for liker in likers:
            account = Account()
            account.igname = liker.username
            account.save()
        return Response(likers)

    @action(detail=True, methods=["get"], url_path="retrieve-commenters")
    def retrieve_commenters(self, request, pk=None):
        reel = self.get_object()
        cl = login_user()

        media_pk = cl.media_pk_from_url(reel.link)
        comments = cl.media_comments(media_pk)
        for comment in comments:
            account = Account()
            account.igname = comment.user.username
            account.save()
        return Response(comments)

    @action(detail=False, methods=["post"], url_path="batch-uploads")
    def batch_uploads(self, request):
        serializer = UploadSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)

        if valid:
            paramFile = io.TextIOWrapper(request.FILES["file_uploaded"].file)
            portfolio1 = csv.DictReader(paramFile)
            list_of_dict = list(portfolio1)
            objs = [Reel(id=PushID().next_id(), link=row["link"]) for row in list_of_dict]
            try:
                msg = Reel.objects.bulk_create(objs)
                returnmsg = {"status_code": 200}
                print(f"imported {msg} successfully")
            except Exception as e:
                print("Error While Importing Data: ", e)
                returnmsg = {"status_code": 500}

            return Response(returnmsg)

        else:
            return Response({"status_code": 500})


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

    def get_serializer_class(self):
        if self.action == "batch_uploads":
            return UploadSerializer
        elif self.action == "add_comment":
            return AddCommentSerializer
        return self.serializer_class

    @action(detail=True, methods=["get"], url_path="fetch-comments")
    def fetch_comments(self, request, pk=None):
        try:
            story = self.get_object()
            cl = login_user()
            media_pk = cl.media_pk_from_url(story.link)
            media_id = cl.media_id(media_pk=media_pk)
            comments = cl.media_comments(media_id=media_id)
            response = {"comments": comments, "length": len(comments)}
            return Response(response, status=status.HTTP_200_OK)
        except Exception as error:
            error_message = str(error)
            return Response({"error": error_message})

    @action(detail=True, methods=["post"], url_path="add-comment")
    def add_comment(self, request, pk=None):
        story = self.get_object()
        cl = login_user()

        media_pk = cl.media_pk_from_url(story.link)
        media_id = cl.media_id(media_pk=media_pk)
        serializer = AddCommentSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)
        generated_response = detect_intent(
            project_id="boostedchatapi",
            session_id=str(uuid.uuid4()),
            message=serializer.data.get("text"),
            language_code="en",
        )
        if valid:
            cl.media_comment(media_id, generated_response)

        return Response({"status": status.HTTP_200_OK, "message": generated_response, "success": True})

    @action(detail=True, methods=["get"], url_path="retrieve-info")
    def like_story(self, request, pk=None):
        story = self.get_object()
        cl = login_user()
        story_pk = cl.story_pk_from_url(story.link)
        info = cl.story_info(story_pk)
        cl.story_like(story_id=info.id)
        return Response({"status": status.HTTP_200_OK, "success": True})

    @action(detail=True, methods=["get"], url_path="retrieve-info")
    def retrieve_info(self, request, pk=None):
        story = self.get_object()
        cl = login_user()

        story_pk = cl.story_pk_from_url(story.link)
        info = cl.story_info(story_pk).dict()
        return Response(info)

    @action(detail=False, methods=["post"], url_path="batch-uploads")
    def batch_uploads(self, request):
        serializer = UploadSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)

        if valid:
            paramFile = io.TextIOWrapper(request.FILES["file_uploaded"].file)
            portfolio1 = csv.DictReader(paramFile)
            list_of_dict = list(portfolio1)
            objs = [Story(id=PushID().next_id(), link=row["link"]) for row in list_of_dict]
            try:
                msg = Story.objects.bulk_create(objs)
                returnmsg = {"status_code": 200}
                print(f"imported {msg} successfully")
            except Exception as e:
                print("Error While Importing Data: ", e)
                returnmsg = {"status_code": 500}

            return Response(returnmsg)

        else:
            return Response({"status_code": 500})
