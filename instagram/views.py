# Create your views here.
import csv
import io
import json
import logging
import uuid
from datetime import date, datetime, timedelta
from urllib.parse import urlparse

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_celery_beat.models import CrontabSchedule, PeriodicTask
from instagrapi.exceptions import UserNotFound
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from base.helpers.push_id import PushID
from data.helpers.random_data import get_random_compliment
from dialogflow.helpers.intents import detect_intent
from instagram.helpers.llm import query_gpt
from instagram.helpers.login import login_user

from .models import Account, Comment, HashTag, Photo, Reel, StatusCheck, Story, Thread, Video
from .serializers import (
    AccountSerializer,
    AddContentSerializer,
    CommentSerializer,
    HashTagSerializer,
    PhotoSerializer,
    ReelSerializer,
    StorySerializer,
    ThreadSerializer,
    UploadSerializer,
    VideoSerializer,
)
from .tasks import follow_user, send_comment, send_message


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

    def list(self, request, *args, **kwargs):

        accounts = self.queryset.values()
        # import pdb;pdb.set_trace()

        return Response({"accounts": accounts})

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

    @action(detail=False, methods=["get"], url_path="needs-assessment", url_name="needs_assesment")
    def send_to_needs_assessment(self, request):

        account = self.get_object()
        account.stage = 2
        account.save()
        return Response({"stage": 2, "success": True})


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
            return AddContentSerializer
        return self.serializer_class

    def perform_create(self, request, *args, **kwargs):
        cl = login_user()
        serializer = self.get_serializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)
        photo = Photo(**serializer.data)
        if valid:
            media_pk = cl.media_pk_from_url(serializer.data.get("link"))
            user = cl.media_user(media_pk=media_pk)
            account = Account.objects.filter(igname=user.username)
            if account.exists():
                photo.account = account.last()
                photo.save()
            else:
                account = Account()
                account.igname = user.username
                account.save()
                photo.save()

        return Response({"data": serializer.data})

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

            response = {"comments": comments, "length": len(comments), "owner": photo.account.igname}
            return Response(response, status=status.HTTP_200_OK)
        except Exception as error:
            error_message = str(error)
            return Response({"error": error_message})

    @action(detail=True, methods=["post"], url_path="generate-comment")
    def generate_comment(self, request, pk=None):
        photo = self.get_object()
        generated_response = detect_intent(
            project_id="boostedchatapi",
            session_id=str(uuid.uuid4()),
            message=request.data.get("text"),
            language_code="en",
        )
        return Response(
            {
                "status": status.HTTP_200_OK,
                "generated_comment": generated_response,
                "text": request.data.get("text"),
                "photo": photo.link,
                "success": True,
            }
        )

    @action(detail=True, methods=["post"], url_path="add-comment")
    def add_comment(self, request, pk=None):
        photo = self.get_object()
        serializer = AddContentSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)
        generated_response = serializer.data.get("generated_response")
        if valid and serializer.data.get("assign_robot") and serializer.data.get("approve"):
            send_comment.delay(photo.link, generated_response)
            return Response({"status": status.HTTP_200_OK, "message": generated_response, "success": True})
        else:
            send_comment.delay(photo.link, serializer.data.get("human_response"))
            return Response(
                {"status": status.HTTP_200_OK, "message": serializer.data.get("human_response"), "success": True}
            )

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
            return AddContentSerializer
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

    @action(detail=True, methods=["post"], url_path="generate-comment")
    def generate_comment(self, request, pk=None):
        video = self.get_object()
        generated_response = detect_intent(
            project_id="boostedchatapi",
            session_id=str(uuid.uuid4()),
            message=request.data.get("text"),
            language_code="en",
        )
        return Response(
            {
                "status": status.HTTP_200_OK,
                "generated_comment": generated_response,
                "text": request.data.get("text"),
                "video": video.link,
                "success": True,
            }
        )

    @action(detail=True, methods=["post"], url_path="add-comment")
    def add_comment(self, request, pk=None):
        video = self.get_object()
        cl = login_user()

        media_pk = cl.media_pk_from_url(video.link)
        media_id = cl.media_id(media_pk=media_pk)
        serializer = AddContentSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)
        generated_response = serializer.data.get("generated_response")
        if valid and serializer.data.get("assign_robot") and serializer.data.get("approve"):
            send_comment(media_id, generated_response)
            return Response({"status": status.HTTP_200_OK, "message": generated_response, "success": True})
        else:
            send_comment(media_id, serializer.data.get("human_response"))
            return Response(
                {"status": status.HTTP_200_OK, "message": serializer.data.get("human_response"), "success": True}
            )

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
            return AddContentSerializer

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

    @action(detail=True, methods=["post"], url_path="generate-comment")
    def generate_comment(self, request, pk=None):
        reel = self.get_object()
        generated_response = detect_intent(
            project_id="boostedchatapi",
            session_id=str(uuid.uuid4()),
            message=request.data.get("text"),
            language_code="en",
        )
        return Response(
            {
                "status": status.HTTP_200_OK,
                "generated_comment": generated_response,
                "text": request.data.get("text"),
                "reel": reel.link,
                "success": True,
            }
        )

    @action(detail=True, methods=["post"], url_path="add-comment")
    def add_comment(self, request, pk=None):
        reel = self.get_object()
        cl = login_user()

        media_pk = cl.media_pk_from_url(reel.link)
        media_id = cl.media_id(media_pk=media_pk)
        serializer = AddContentSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)
        generated_response = serializer.data.get("generated_response")
        if valid and serializer.data.get("assign_robot") and serializer.data.get("approve"):
            cl.media_comment(media_id, generated_response)
            return Response({"status": status.HTTP_200_OK, "message": generated_response, "success": True})
        else:
            cl.media_comment(media_id, serializer.data.get("human_response"))
            return Response(
                {"status": status.HTTP_200_OK, "message": serializer.data.get("human_response"), "success": True}
            )

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
            return AddContentSerializer
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

    @action(detail=True, methods=["post"], url_path="generate-comment")
    def generate_comment(self, request, pk=None):
        story = self.get_object()
        generated_response = detect_intent(
            project_id="boostedchatapi",
            session_id=str(uuid.uuid4()),
            message=request.data.get("text"),
            language_code="en",
        )
        return Response(
            {
                "status": status.HTTP_200_OK,
                "generated_comment": generated_response,
                "text": request.data.get("text"),
                "story": story.link,
                "success": True,
            }
        )

    @action(detail=True, methods=["post"], url_path="add-comment")
    def add_comment(self, request, pk=None):
        story = self.get_object()
        cl = login_user()

        media_pk = cl.media_pk_from_url(story.link)
        media_id = cl.media_id(media_pk=media_pk)
        serializer = AddContentSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)
        generated_response = serializer.data.get("generated_response")
        if valid and serializer.data.get("assign_robot") and serializer.data.get("approve"):
            cl.media_comment(media_id, generated_response)
            return Response({"status": status.HTTP_200_OK, "message": generated_response, "success": True})
        else:
            cl.media_comment(media_id, serializer.data.get("human_response"))
            return Response(
                {"status": status.HTTP_200_OK, "message": serializer.data.get("human_response"), "success": True}
            )

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


class DMViewset(viewsets.ModelViewSet):
    queryset = Thread.objects.all()
    serializer_class = ThreadSerializer

    def get_serializer_class(self):
        if self.action == "send_message":
            return AddContentSerializer
        elif self.action == "generate_response":
            return AddContentSerializer
        return self.serializer_class

    @action(detail=True, methods=["get"], url_path="fetch-messages")
    def fetch_messages(self, request, pk=None):
        thread = self.get_object()
        cl = login_user()
        message_info = []
        try:

            # Iterate through the threads and access messages
            messages = cl.direct_messages(thread_id=thread.thread_id)

            for message in messages:
                message_response = {
                    "username": cl.username_from_user_id(message.user_id),
                    "text": message.text,
                    "timestamp": message.timestamp,
                }
                message_info.append(message_response)
            return Response(message_info, status=status.HTTP_200_OK)
        except Exception as error:
            error_message = str(error)
            return Response({"error": error_message})

    @action(detail=True, methods=["post"], url_path="generate-response")
    def generate_response(self, request, pk=None):
        thread = self.get_object()
        generated_response = None
        if thread.account.status.name == "responded_to_first_compliment":
            try:
                followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread.account.igname}")
                followup_task.delete()
            except Exception as error:
                print(error)

            enforced_shared_compliment = query_gpt(
                f"""
                respond the following dm within the triple backticks
                ```{request.data.get("text")}``` in a friendly tone
                """
            )
            print(enforced_shared_compliment)
            generated_response = enforced_shared_compliment.get("choices")[0].get("text")
            print(thread.account.igname)
            follow_user.delay(thread.account.igname)
            statuscheck, _ = StatusCheck.objects.update_or_create(stage=2, name="preparing_to_send_first_question")
            print(statuscheck)
            account = Account.objects.get(id=thread.account.id)
            print(account.status)
            account.status = statuscheck
            account.save()

            print(account.status)
        elif thread.account.status.name == "sent_first_question":
            try:
                followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread.account.igname}")
                followup_task.delete()
            except Exception as error:
                print(error)

            rephrase_defined_problem = query_gpt(
                f"""
                rephrase the problem stated in the followin dm within the triple backticks
                ```{request.data.get("text")}``` in a friendly tone add emoji that indicate
                you are in sympathy with them
                """
            )
            generated_response = rephrase_defined_problem.get("choices")[0].get("text")
            statuscheck, _ = StatusCheck.objects.update_or_create(stage=2, name="preparing_to_send_second_question")
            account = get_object_or_404(Account, id=thread.account.id)
            account.status = statuscheck
            account.save()
        elif thread.account.status.name == "sent_second_question":
            last_seven_days = [date.today() - timedelta(days=day) for day in range(7)]
            if thread.account.outsourced:
                if thread.account.outsourced.updated_at.date() in last_seven_days:
                    pass
            else:
                followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread.account.igname}")
                followup_task.delete()

                rephrase_defined_problem = query_gpt(
                    f"""
                    rephrase the importance stated in the following dm within the triple backticks
                    ```{request.data.get("text")}``` in a friendly tone add emoji that indicate
                    you are affirming what they are saying
                    """
                )
                generated_response = rephrase_defined_problem.get("choices")[0].get("text")
                statuscheck, _ = StatusCheck.objects.update_or_create(stage=2, name="preparing_to_send_third_question")
                account = get_object_or_404(Account, id=thread.account.id)
                account.status = statuscheck
                account.save()
        elif thread.account.status.name == "sent_third_question":
            booking_system = None
            last_seven_days = [date.today() - timedelta(days=day) for day in range(7)]
            if booking_system and thread.account.outsourced.updated_at.date() in last_seven_days:
                pass
            else:
                followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread.account.igname}")
                followup_task.delete()

                rephrase_defined_problem = query_gpt(
                    f"""
                    respond to the following dm within the triple backticks
                    ```{request.data.get("text")}``` in a way that shows that you have understood them.
                    """
                )
                generated_response = rephrase_defined_problem.get("choices")[0].get("text")
                statuscheck, _ = StatusCheck.objects.update_or_create(
                    stage=2, name="preparing_to_send_first_needs_assessment_question"
                )
                account = get_object_or_404(Account, id=thread.account.id)
                account.status = statuscheck
                account.save()
        elif thread.account.status.name == "sent_first_needs_assessment_question":
            confirm_reject_problem = True
            if confirm_reject_problem:
                try:
                    followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread.account.igname}")
                    followup_task.delete()
                except Exception as error:
                    print(error)

                rephrase_defined_problem = query_gpt(
                    f"""
                    respond to the following dm within the triple backticks
                    ```{request.data.get("text")}``` in a way that shows that you have understood them.
                    """
                )
                generated_response = rephrase_defined_problem.get("choices")[0].get("text")
                statuscheck, _ = StatusCheck.objects.update_or_create(
                    stage=2, name="preparing_to_send_second_needs_assessment_question"
                )
                account = get_object_or_404(Account, id=thread.account.id)
                account.status = statuscheck
                account.save()
            else:
                pass

        elif thread.account.status.name == "sent_second_needs_assessment_question":
            confirm_reject_problem = True
            if confirm_reject_problem:

                try:
                    followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread.account.igname}")
                    followup_task.delete()
                except Exception as error:
                    print(error)

                rephrase_defined_problem = query_gpt(
                    f"""
                    respond to the following dm within the triple backticks
                    ```{request.data.get("text")}``` in a way that shows that you have understood them.
                    """
                )
                generated_response = rephrase_defined_problem.get("choices")[0].get("text")
                statuscheck, _ = StatusCheck.objects.update_or_create(
                    stage=2, name="preparing_to_send_third_needs_assessment_question"
                )
                account = get_object_or_404(Account, id=thread.account.id)
                account.status = statuscheck
                account.save()
            else:
                pass
        elif thread.account.status.name == "sent_third_needs_assessment_question":
            confirm_reject_problem = True
            if confirm_reject_problem:
                try:
                    followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread.account.igname}")
                    followup_task.delete()
                except Exception as error:
                    print(error)

                rephrase_defined_problem = query_gpt(
                    f"""
                    respond to the following dm within the triple backticks
                    ```{request.data.get("text")}``` in a way that shows that you have understood them.
                    """
                )
                generated_response = rephrase_defined_problem.get("choices")[0].get("text")
                statuscheck, _ = StatusCheck.objects.update_or_create(stage=2, name="follow_up_after_presentation")
                account = get_object_or_404(Account, id=thread.account.id)
                account.status = statuscheck
                account.save()
            else:
                pass

        elif thread.account.status.name == "sent_follow_up_presentation":
            check_email = True
            if check_email:
                try:
                    followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread.account.igname}")
                    followup_task.delete()
                except Exception as error:
                    print(error)

                rephrase_defined_problem = query_gpt(
                    f"""
                    respond to the following dm within the triple backticks
                    ```{request.data.get("text")}``` in a way that shows that you have understood them.
                    """
                )
                generated_response = rephrase_defined_problem.get("choices")[0].get("text")
                statuscheck, _ = StatusCheck.objects.update_or_create(stage=2, name="ask_for_email_first_attempt")
                account = get_object_or_404(Account, id=thread.account.id)
                account.status = statuscheck
                account.save()
            else:
                interested = query_gpt(
                    f"""
                    analyse to the following dm within the triple backticks
                    ```{request.data.get("text")}``` to know whether they are interested in the
                    product or not and return
                    a boolean of 0 -if not interested, and 1 -if interested and 2 -if have any objections.
                    """
                )
                if int(interested) == 1:
                    pass

                elif int(interested) == 0:
                    rephrase_defined_problem = query_gpt(
                        f"""
                        rephrase the following dm within the triple backticks
                        ```{request.data.get("text")}``` asking them why they are not interested.
                        """
                    )
                    generated_response = rephrase_defined_problem.get("choices")[0].get("text")
                    statuscheck, _ = StatusCheck.objects.update_or_create(stage=3, name="ask_uninterest")
                    account = get_object_or_404(Account, id=thread.account.id)
                    account.status = statuscheck
                    account.save()
                elif int(interested) == 2:
                    rephrase_defined_problem = query_gpt(
                        f"""
                        rephrase objection within the triple backticks
                        ```{request.data.get("text")}``` in a way
                        to show that they’re understood
                        """
                    )
                    generated_response = rephrase_defined_problem.get("choices")[0].get("text")
                    statuscheck, _ = StatusCheck.objects.update_or_create(stage=3, name="ask_objection")
                    account = get_object_or_404(Account, id=thread.account.id)
                    account.status = statuscheck
                    account.save()

        else:
            generated_response = detect_intent(
                project_id="boostedchatapi",
                session_id=str(uuid.uuid4()),
                message=request.data.get("text"),
                language_code="en",
            )
        thread.replied = False
        thread.save()
        return Response(
            {
                "status": status.HTTP_200_OK,
                "generated_comment": generated_response,
                "text": request.data.get("text"),
                "success": True,
                "replied": thread.replied,
            }
        )

    @action(detail=False, methods=["get"], url_path="check-response")
    def check_response(self, request, pk=None):

        try:

            daily_schedule, _ = CrontabSchedule.objects.get_or_create(
                minute="*/4",
                hour="*",
                day_of_week="*",
                day_of_month="*",
                month_of_year="*",
            )
            monthly_schedule, _ = CrontabSchedule.objects.get_or_create(
                minute="*/6",
                hour="*",
                day_of_week="*",
                day_of_month="*",
                month_of_year="*",
            )
            for thread_ in self.queryset.all():
                if thread_.account.status.name == "responded_to_first_compliment":
                    pass
                elif thread_.account.status.name == "sent_first_compliment":
                    salesrep = thread_.account.salesrep_set.get(instagram=thread_.account)
                    random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
                    task = None
                    try:
                        task, _ = PeriodicTask.objects.get_or_create(
                            name=f"FollowupTask-{thread_.account.igname}",
                            crontab=daily_schedule,
                            task="instagram.tasks.send_message",
                            args=json.dumps([[random_compliment], [thread_.thread_id]]),
                            start_time=timezone.now(),
                        )
                    except Exception as error:
                        task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
                        task.args = json.dumps([[random_compliment], [thread_.thread_id]])
                        task.save()
                        logging.warning(str(error))

                    if timezone.now() >= task.start_time + timedelta(minutes=4):
                        followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
                        followup_task.crontab = monthly_schedule
                        followup_task.save()
                elif thread_.account.status.name == "sent_first_question":
                    salesrep = thread_.account.salesrep_set.get(instagram=thread_.account)
                    random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
                    task = None
                    try:
                        task, _ = PeriodicTask.objects.get_or_create(
                            name=f"FollowupTask-{thread_.account.igname}",
                            crontab=daily_schedule,
                            task="instagram.tasks.send_message",
                            args=json.dumps([[random_compliment], [thread_.thread_id]]),
                            start_time=timezone.now(),
                        )
                    except Exception as error:
                        task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
                        task.args = json.dumps([[random_compliment], [thread_.thread_id]])
                        task.save()
                        logging.warning(str(error))

                    if timezone.now() >= task.start_time + timedelta(minutes=4):
                        followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
                        followup_task.crontab = monthly_schedule
                        followup_task.save()

                elif thread_.account.status.name == "sent_second_question":

                    salesrep = thread_.account.salesrep_set.get(instagram=thread_.account)
                    random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
                    task = None
                    try:
                        task, _ = PeriodicTask.objects.get_or_create(
                            name=f"FollowupTask-{thread_.account.igname}",
                            crontab=daily_schedule,
                            task="instagram.tasks.send_message",
                            args=json.dumps([[random_compliment], [thread_.thread_id]]),
                            start_time=timezone.now(),
                        )
                    except Exception as error:
                        task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
                        task.args = json.dumps([[random_compliment], [thread_.thread_id]])
                        task.save()
                        logging.warning(str(error))

                    if timezone.now() >= task.start_time + timedelta(minutes=4):
                        followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
                        followup_task.crontab = monthly_schedule
                        followup_task.save()

                elif thread_.account.status.name == "sent_third_question":

                    salesrep = thread_.account.salesrep_set.get(instagram=thread_.account)
                    random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
                    task = None
                    try:
                        task, _ = PeriodicTask.objects.get_or_create(
                            name=f"FollowupTask-{thread_.account.igname}",
                            crontab=daily_schedule,
                            task="instagram.tasks.send_message",
                            args=json.dumps([[random_compliment], [thread_.thread_id]]),
                            start_time=timezone.now(),
                        )
                    except Exception as error:
                        task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
                        task.args = json.dumps([[random_compliment], [thread_.thread_id]])
                        task.save()
                        logging.warning(str(error))

                    if timezone.now() >= task.start_time + timedelta(minutes=4):
                        followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
                        followup_task.crontab = monthly_schedule
                        followup_task.save()

                elif thread_.account.status.name == "sent_first_needs_assessment_question":

                    salesrep = thread_.account.salesrep_set.get(instagram=thread_.account)
                    random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
                    task = None
                    try:
                        task, _ = PeriodicTask.objects.get_or_create(
                            name=f"FollowupTask-{thread_.account.igname}",
                            crontab=daily_schedule,
                            task="instagram.tasks.send_message",
                            args=json.dumps([[random_compliment], [thread_.thread_id]]),
                            start_time=timezone.now(),
                        )
                    except Exception as error:
                        task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
                        task.args = json.dumps([[random_compliment], [thread_.thread_id]])
                        task.save()
                        logging.warning(str(error))

                    if timezone.now() >= task.start_time + timedelta(minutes=4):
                        followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
                        followup_task.crontab = monthly_schedule
                        followup_task.save()

                elif thread_.account.status.name == "sent_second_needs_assessment_question":

                    salesrep = thread_.account.salesrep_set.get(instagram=thread_.account)
                    random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
                    task = None
                    try:
                        task, _ = PeriodicTask.objects.get_or_create(
                            name=f"FollowupTask-{thread_.account.igname}",
                            crontab=daily_schedule,
                            task="instagram.tasks.send_message",
                            args=json.dumps([[random_compliment], [thread_.thread_id]]),
                            start_time=timezone.now(),
                        )
                    except Exception as error:
                        task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
                        task.args = json.dumps([[random_compliment], [thread_.thread_id]])
                        task.save()
                        logging.warning(str(error))

                    if timezone.now() >= task.start_time + timedelta(minutes=4):
                        followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
                        followup_task.crontab = monthly_schedule
                        followup_task.save()

                elif thread_.account.status.name == "sent_third_needs_assessment_question":

                    salesrep = thread_.account.salesrep_set.get(instagram=thread_.account)
                    random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
                    task = None
                    try:
                        task, _ = PeriodicTask.objects.get_or_create(
                            name=f"FollowupTask-{thread_.account.igname}",
                            crontab=daily_schedule,
                            task="instagram.tasks.send_message",
                            args=json.dumps([[random_compliment], [thread_.thread_id]]),
                            start_time=timezone.now(),
                        )
                    except Exception as error:
                        task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
                        task.args = json.dumps([[random_compliment], [thread_.thread_id]])
                        task.save()
                        logging.warning(str(error))

                    if timezone.now() >= task.start_time + timedelta(minutes=4):
                        followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
                        followup_task.crontab = monthly_schedule
                        followup_task.save()

                elif thread_.account.status.name == "sent_follow_up_after_presentation":
                    if thread_.account.dormant_profile_created:
                        booksy_status, _ = StatusCheck.objects.get_or_create(stage=2, name="Trial")

                        account = get_object_or_404(Account, id=thread_.account.id)
                        account.status = booksy_status
                        account.save()

                        salesrep = thread_.account.salesrep_set.get(instagram=thread_.account)

                        random_compliment = f""""
                            What's up {thread_.account.igname} let us make the most of your free trial account?
                            you can manage it all with https://dl.booksy.com/WSlwk9kUhCb
                            (login: {thread_.account.igname} password: {str(uuid.uuid4())}) to
                            [solution to combination of problems]
                            DM: let me know what you think and I’ll guide you for a month to grow it like crazy:)
                            """
                        task = None
                        try:
                            task, _ = PeriodicTask.objects.get_or_create(
                                name=f"FollowupTask-{thread_.account.igname}",
                                crontab=daily_schedule,
                                task="instagram.tasks.send_message",
                                args=json.dumps([[random_compliment], [thread_.thread_id]]),
                                start_time=timezone.now(),
                            )
                        except Exception as error:
                            task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
                            task.args = json.dumps([[random_compliment], [thread_.thread_id]])
                            task.save()
                            logging.warning(str(error))

                        if timezone.now() >= task.start_time + timedelta(minutes=4):
                            followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
                            followup_task.crontab = monthly_schedule
                            followup_task.save()
                elif thread_.account.status.name == "sent_email_first_attempt":
                    # compiled from llm
                    combination_of_problems = []
                    salesrep = thread_.account.salesrep_set.get(instagram=thread_.account)
                    random_compliment = f"""
                        I actually think Booksy will help you big time {combination_of_problems}
                        Let me know your email address and I’ll help you with the setup;)
                        """
                    task = None
                    try:
                        task, _ = PeriodicTask.objects.get_or_create(
                            name=f"FollowupTask-{thread_.account.igname}",
                            crontab=daily_schedule,
                            task="instagram.tasks.send_message",
                            args=json.dumps([[random_compliment], [thread_.thread_id]]),
                            start_time=timezone.now(),
                        )
                    except Exception as error:
                        task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
                        task.args = json.dumps([[random_compliment], [thread_.thread_id]])
                        task.save()
                        logging.warning(str(error))

                    if timezone.now() >= task.start_time + timedelta(minutes=4):
                        second_attempt = """
                            When you see your profile on Booksy you won’t believe that you
                            used to [combination of problems].
                            What’s your valid email address?
                            """
                        followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
                        followup_task.crontab = monthly_schedule
                        task.args = json.dumps([[second_attempt], [thread_.thread_id]])
                        followup_task.save()

                        status_after_response, _ = StatusCheck.objects.get_or_create(
                            stage=2, name="sent_email_second_attempt"
                        )
                        account = get_object_or_404(Account, id=thread_.account.id)
                        account.status = status_after_response
                        account.save()

                    if timezone.now() >= task.start_time + timedelta(minutes=3):
                        third_attempt = """
                            I can see you’re pretty busy and wanted to create profile on Booksy for you to
                            elevate your business,
                            I’ll just need your email address:)
                            """
                        followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
                        followup_task.crontab = monthly_schedule
                        task.args = json.dumps([[third_attempt], [thread_.thread_id]])
                        followup_task.save()

                        status_after_response, _ = StatusCheck.objects.get_or_create(
                            stage=3, name="sent_email_last_attempt"
                        )
                        account = get_object_or_404(Account, id=thread_.account.id)
                        account.status = status_after_response
                        account.save()

                elif thread_.account.status.name == "sent_uninterest":

                    salesrep = thread_.account.salesrep_set.get(instagram=thread_.account)
                    rephrase_defined_problem = query_gpt(
                        """
                            ask for the more detailed reason why they are not interested
                            """
                    )
                    random_compliment = rephrase_defined_problem.get("choices")[0].get("text")
                    task = None
                    try:
                        task, _ = PeriodicTask.objects.get_or_create(
                            name=f"FollowupTask-{thread_.account.igname}",
                            crontab=daily_schedule,
                            task="instagram.tasks.send_message",
                            args=json.dumps([[random_compliment], [thread_.thread_id]]),
                            start_time=timezone.now(),
                        )
                    except Exception as error:
                        task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
                        task.args = json.dumps([[random_compliment], [thread_.thread_id]])
                        task.save()
                        logging.warning(str(error))

                    if timezone.now() >= task.start_time + timedelta(minutes=4):
                        followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
                        followup_task.crontab = monthly_schedule
                        followup_task.save()

                elif thread_.account.status.name == "sent_objection":

                    salesrep = thread_.account.salesrep_set.get(instagram=thread_.account)
                    random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
                    task = None
                    try:
                        task, _ = PeriodicTask.objects.get_or_create(
                            name=f"FollowupTask-{thread_.account.igname}",
                            crontab=daily_schedule,
                            task="instagram.tasks.send_message",
                            args=json.dumps([[random_compliment], [thread_.thread_id]]),
                            start_time=timezone.now(),
                        )
                    except Exception as error:
                        task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
                        task.args = json.dumps([[random_compliment], [thread_.thread_id]])
                        task.save()
                        logging.warning(str(error))

                    if timezone.now() >= task.start_time + timedelta(minutes=4):
                        followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
                        followup_task.crontab = monthly_schedule
                        followup_task.save()

            return Response({"success": True}, status=status.HTTP_200_OK)
        except Exception as error:
            return Response({"error": str(error)})

    @action(detail=True, methods=["post"], url_path="send-message")
    def send_message(self, request, pk=None):
        thread = self.get_object()
        serializer = AddContentSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)
        generated_response = serializer.data.get("generated_response")
        if valid and serializer.data.get("assign_robot") and serializer.data.get("approve"):

            response_status = Thread.objects.filter(account__status__name="sent_first_compliment")
            if response_status.exists():
                send_message.delay(generated_response, thread_id=thread.thread_id)
                thread.replied = True
                thread.replied_at = datetime.now()
                status_after_response, _ = StatusCheck.objects.get_or_create(
                    stage=1, name="responded_to_first_compliment"
                )
                account = get_object_or_404(Account, id=thread.account.id)
                account.status = status_after_response
                account.save()

            response_status = Thread.objects.filter(account__status__name="preparing_to_send_first_question")
            if response_status.exists():
                send_message.delay(
                    f"""
                    {generated_response},
                    I hope you don't mind me also asking,
                    I was wondering what's the gnarliest part of your barber gig?
                    """,
                    thread_id=thread.thread_id,
                )
                thread.replied = True
                thread.replied_at = datetime.now()
                status_after_response, _ = StatusCheck.objects.get_or_create(stage=2, name="sent_first_question")
                account = get_object_or_404(Account, id=thread.account.id)
                account.status = status_after_response
                account.save()

            response_status = Thread.objects.filter(account__status__name="preparing_to_send_second_question")
            if response_status.exists():
                send_message.delay(
                    f"""
                    {generated_response}
                    I was also thinking about asking,
                    How about your clients? Is managing current ones
                    more difficult than attracting new clients?
                    """,
                    thread_id=thread.thread_id,
                )
                thread.replied = True
                thread.replied_at = datetime.now()
                status_after_response, _ = StatusCheck.objects.get_or_create(stage=2, name="sent_second_question")
                account = get_object_or_404(Account, id=thread.account.id)
                account.status = status_after_response
                account.save()

            response_status = Thread.objects.filter(account__status__name="preparing_to_send_third_question")
            if response_status.exists():
                send_message.delay(
                    f"""
                    {generated_response},
                    by the way could you please help me understand,
                    How do you manage your calendar?
                    """,
                    thread_id=thread.thread_id,
                )
                thread.replied = True
                thread.replied_at = datetime.now()
                status_after_response, _ = StatusCheck.objects.get_or_create(stage=2, name="sent_third_question")
                account = get_object_or_404(Account, id=thread.account.id)
                account.status = status_after_response
                account.save()

            response_status = Thread.objects.filter(
                account__status__name="preparing_to_send_first_needs_assessment_question"
            )
            if response_status.exists():
                send_message.delay(
                    f"""
                    {generated_response}
                    besides I would like to notify you that,
                    Seems like you are starting a great career, {thread.account.igname} 🔥
                    If you don’t mind me asking... How do you market yourself? 🤔
                    """,
                    thread_id=thread.thread_id,
                )
                thread.replied = True
                thread.replied_at = datetime.now()
                status_after_response, _ = StatusCheck.objects.get_or_create(
                    stage=2, name="sent_first_needs_assessment_question"
                )
                account = get_object_or_404(Account, id=thread.account.id)
                account.status = status_after_response
                account.save()

            response_status = Thread.objects.filter(
                account__status__name="preparing_to_send_second_needs_assessment_question"
            )
            if response_status.exists():
                send_message.delay(
                    f"""
                    {generated_response}
                    I was also thinking of asking,
                    Did you consider social post creator tools to make your IG account more visible? you
                    have amazing potential and could easily convert your followers into clients with IG Book Button
                    """,
                    thread_id=thread.thread_id,
                )
                thread.replied = True
                thread.replied_at = datetime.now()
                status_after_response, _ = StatusCheck.objects.get_or_create(
                    stage=2, name="sent_second_needs_assessment_question"
                )
                account = get_object_or_404(Account, id=thread.account.id)
                account.status = status_after_response
                account.save()

            response_status = Thread.objects.filter(
                account__status__name="preparing_to_send_third_needs_assessment_question"
            )
            if response_status.exists():
                send_message.delay(
                    f"""
                    {generated_response}
                    by the way,
                    Returning clients are critical for long-term success,
                    are you able to invite back to your chair the clients who stopped booking? 🤔
                    """,
                    thread_id=thread.thread_id,
                )
                thread.replied = True
                thread.replied_at = datetime.now()
                status_after_response, _ = StatusCheck.objects.get_or_create(
                    stage=2, name="sent_third_needs_assessment_question"
                )
                account = get_object_or_404(Account, id=thread.account.id)
                account.status = status_after_response
                account.save()

            response_status = Thread.objects.filter(account__status__name="follow_up_after_presentation")
            if response_status.exists():
                send_message.delay(
                    f"""
                    {generated_response}
                    I hope you are comfortable with me asking,
                    What do you think about booksy? would you like to give it a try?
                    """,
                    thread_id=thread.thread_id,
                )
                thread.replied = True
                thread.replied_at = datetime.now()
                status_after_response, _ = StatusCheck.objects.get_or_create(
                    stage=2, name="sent_follow_up_after_presentation"
                )
                account = get_object_or_404(Account, id=thread.account.id)
                account.status = status_after_response
                account.save()

            response_status = Thread.objects.filter(account__status__name="ask_for_email_first_attempt")
            if response_status.exists():
                send_message.delay(
                    f"""
                    {generated_response}
                    consider also this that,
                    I can quickly setup an account for you to check it out - what’s your email address?
                    The one you use on IG will help with IG book button
                    """,
                    thread_id=thread.thread_id,
                )
                thread.replied = True
                thread.replied_at = datetime.now()
                status_after_response, _ = StatusCheck.objects.get_or_create(stage=2, name="sent_email_first_attempt")
                account = get_object_or_404(Account, id=thread.account.id)
                account.status = status_after_response
                account.save()

            response_status = Thread.objects.filter(account__status__name="ask_uninterest")
            if response_status.exists():
                send_message.delay(
                    generated_response,
                    thread_id=thread.thread_id,
                )
                thread.replied = True
                thread.replied_at = datetime.now()
                status_after_response, _ = StatusCheck.objects.get_or_create(stage=2, name="sent_uninterest")
                account = get_object_or_404(Account, id=thread.account.id)
                account.status = status_after_response
                account.save()

            response_status = Thread.objects.filter(account__status__name="ask_objection")
            if response_status.exists():
                send_message.delay(
                    generated_response,
                    thread_id=thread.thread_id,
                )
                thread.replied = True
                thread.replied_at = datetime.now()
                status_after_response, _ = StatusCheck.objects.get_or_create(stage=2, name="sent_objection")
                account = get_object_or_404(Account, id=thread.account.id)
                account.status = status_after_response
                account.save()

            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "message": generated_response,
                    "thread_id": thread.thread_id,
                    "success": True,
                }
            )
        else:
            send_message.delay(serializer.data.get("human_response"), thread_id=thread.thread_id)
            response_status = Thread.objects.filter(account__status__name="sent_first_compliment")
            thread.replied = True
            thread.replied_at = datetime.now()
            if response_status.exists():
                thread.account.status.name = "responded_to_first_compliment"
                thread.save()
            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "message": serializer.data.get("human_response"),
                    "thread_id": thread.thread_id,
                    "success": True,
                    "replied": thread.replied,
                    "replied_at": thread.replied_at,
                }
            )
