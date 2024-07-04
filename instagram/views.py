# Create your views here.
import csv
import io
import logging
import uuid
import json
import requests
import random
from urllib.parse import urlparse
from auditlog.models import LogEntry
from datetime import datetime
from instagrapi.exceptions import UserNotFound
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django_celery_beat.models import PeriodicTask


from base.helpers.push_id import PushID
from dialogflow.helpers.get_prompt_responses import get_gpt_response

from django_celery_beat.models import CrontabSchedule, PeriodicTask
from dialogflow.helpers.intents import detect_intent
from instagram.helpers.login import login_user
from sales_rep.models import SalesRep

from .helpers.init_db import init_db
from .models import Account, Comment, HashTag, Photo, Reel, Story, Thread, Video, Message, OutSourced
from .serializers import (
    AccountSerializer,
    OutSourcedSerializer,
    AddContentSerializer,
    CommentSerializer,
    HashTagSerializer,
    PhotoSerializer,
    ReelSerializer,
    SingleThreadSerializer,
    StorySerializer,
    ThreadSerializer,
    UploadSerializer,
    VideoSerializer,
    MessageSerializer,
    SendManualMessageSerializer,
    GetAccountSerializer,
    GetSingleAccountSerializer,
    ScheduleOutreachSerializer
)


class PaginationClass(PageNumberPagination):
    page_size = 20  # Set the number of items per page
    page_size_query_param = 'page_size'
    max_page_size = 100

class OutSourcedViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    queryset = OutSourced.objects.filter(account__isnull=False)
    serializer_class = OutSourcedSerializer
    # import pdb;pdb.set_trace()
    pagination_class = PaginationClass
    
class AccountViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    queryset = Account.objects.all()
    serializer_class = AccountSerializer
    pagination_class = PaginationClass

    def get_serializer_class(self):
        if self.action == "batch_uploads":
            return UploadSerializer
        elif self.action == "retrieve":
            return GetSingleAccountSerializer
        elif self.action == "update":  # override update serializer
            return GetAccountSerializer
        elif self.action == "schedule-outreach":
            return ScheduleOutreachSerializer
        return self.serializer_class

    def list(self, request, *args, **kwargs):

        accounts = []
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(self.queryset, request)
        for account in result_page:
            periodic_task = None
            try:
                periodic_task = PeriodicTask.objects.get(name=f"SendFirstCompliment-{account.igname}")
            except PeriodicTask.DoesNotExist:
                pass

            account_ = {
                "id": account.id,
                "assigned_to": account.assigned_to,
                "confirmed_problems": account.confirmed_problems,
                "full_name": account.full_name or None,
                "igname": account.igname,
                "status": account.status.name if account.status else None,
                "outreach": periodic_task.crontab.human_readable if periodic_task else ""

            }
            accounts.append(account_)
        response_data = {
            'count': paginator.page.paginator.count,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'results': accounts,
        }
        return Response(response_data,status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        queryset = Account.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = GetSingleAccountSerializer(user)
        return Response(serializer.data)

    @action(detail=True,methods=["post"],url_path="add-outsourced")
    def add_outsourced(self,request,pk=None):
        account = self.get_object()
        outsourced_json = request.data.get("results")
        outsourced_source = request.data.get("source")
        outsourced = OutSourced.objects.create(source=outsourced_source,results=outsourced_json,account=account)
        return Response(
            {
                "message": "outsourced data saved succesfully",
                "id": outsourced.id,
                "result": outsourced.results,
                "source": outsourced.source
            }
        )


    @action(detail=False,methods=['post'],url_path='qualify-account')
    def qualify_account(self, request, pk=None):
        accounts = Account.objects.filter(igname = request.data.get('username'))
        accounts_qualified = []
        if accounts.exists():
            for account in accounts:
                if account.outsourced_set.exists():
                    account.qualified = request.data.get('qualify_flag')
                    account.save()
                    accounts_qualified.append(
                        {
                            "qualified":account.qualified,
                            "account_id":account.id
                        }
                    )
        
        return Response(accounts_qualified, status=status.HTTP_200_OK)

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

    @action(detail=True, methods=['post'], url_path="reset-account")
    def reset_account(self, request, pk=None):
        account = self.get_object()

        Thread.objects.filter(account=account).delete()
        account.status = None
        account.confirmed_problems = ""
        account.rejected_problems = ""
        account.save()
        salesReps = SalesRep.objects.filter(instagram=account)
        for salesRep in salesReps:
            salesRep.instagram.remove(account)
        return Response({"message": "Account reset successfully"})

    def account_by_ig_thread_id(self, request, *args, **kwargs):
        thread = Thread.objects.get(thread_id=kwargs.get('ig_thread_id'))
        account = Account.objects.get(pk=thread.account.id)
        serializer = GetSingleAccountSerializer(account)
        return Response(serializer.data)
    
    def retrieve_salesrep(self, request, *args, **kwargs):
        username = kwargs.get('username')

        # Check if username is provided
        if not username:
            return Response({"error": "Username not provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Retrieve the account object or return 404 if not found
        account = Account.objects.filter(igname=username).last()

        # Retrieve the last salesrep associated with the account
        salesrep = account.salesrep_set.last()

        # Check if salesrep is found
        if not salesrep:
            return Response({"error": "Salesrep not found for this account"}, status=status.HTTP_404_NOT_FOUND)

        # Convert salesrep object to dictionary
        salesrep_data = {
            "id": salesrep.id,
            "username": salesrep.ig_username,
        }

        return Response({"salesrep": salesrep_data}, status=status.HTTP_200_OK)
        
            
    @action(detail=True, methods=['post'], url_path="schedule-outreach")
    def schedule_outreach(self, request, pk=None):
        serializer = ScheduleOutreachSerializer(data=request.data)
        valid = serializer.is_valid(raise_exception=True)
        account = self.get_object()
        if valid:
            available_sales_reps = SalesRep.objects.filter(available=True)
            random_salesrep_index = random.randint(0,len(available_sales_reps)-1)
            available_sales_reps[random_salesrep_index].instagram.add(account)

            schedule = CrontabSchedule.objects.create(
                minute=serializer.data.get('minute'),
                hour=serializer.data.get('hour'),
                day_of_week="*",
                day_of_month=serializer.data.get('day_of_month'),
                month_of_year=serializer.data.get('month_of_year'),
            )
            try:
                PeriodicTask.objects.update_or_create(
                    name=f"SendFirstCompliment-{account.igname}",
                    crontab=schedule,
                    task="instagram.tasks.send_first_compliment",
                    args=json.dumps([[account.igname]])
                )
                
            except Exception as error:
                logging.warning(error)

            return Response(serializer.data,status=status.HTTP_200_OK)
        else:
            return Response({"error": True})



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
    pagination_class = PaginationClass

    def get_serializer_class(self):
        if self.action == "send_message":
            return AddContentSerializer
        elif self.action == "generate_response":
            return AddContentSerializer
        return self.serializer_class

    def list(self, request, pk=None):
        assigned_to_filter = request.GET.get("assigned_to")
        stage_filter = request.GET.get("stage")
        salesrep_filter = request.GET.get("sales_rep")
        search_query = request.GET.get("q")
        paginator = self.pagination_class()

        queryset = Thread.objects.select_related('account').order_by("-last_message_at")
        message_data = []
        messages = None

        if stage_filter is not None:
            queryset = queryset.filter(account__index__in=json.loads(stage_filter))
        if assigned_to_filter is not None:
            queryset = queryset.filter(account__assigned_to=assigned_to_filter)
        if salesrep_filter is not None:
            queryset = queryset.filter(account__salesrep__pk__in=json.loads(salesrep_filter))
        if search_query is not None:
            query = Q(account__igname__icontains=search_query) | Q(message__content__icontains=search_query)
            message_query = Q(content__icontains=search_query)
            messages = Message.objects.filter(message_query)
            messages_page = paginator.paginate_queryset(messages, request)
            for message in messages_page:
                message_data.append(
                    {
                        "id": message.id,
                        "thread_pk":message.thread.id,
                        "thread_id":message.thread.thread_id,
                        "content":message.content,
                        "sent_on":message.sent_on,
                        "username": message.thread.account.igname
                    }
                )                

            queryset = queryset.annotate(
                matching_messages_count=Count('message', filter=query)
            )
            queryset = queryset.filter(matching_messages_count__gt=0).distinct()

            
        
        result_page = paginator.paginate_queryset(queryset, request)
        serializer = ThreadSerializer(result_page, many=True)

        response_data = {
            'count': paginator.page.paginator.count,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'results': serializer.data,
            'messages': message_data if search_query is not None else []
        }



        return Response(response_data)

    @action(detail=False, methods=["get"], url_path="handle-duplicates")
    def find_handle_duplicates(self, request):
        duplicate_igname_list = (
            Account.objects.values('igname')
            .annotate(igname_count=Count('igname'))
            .filter(igname_count__gt=1)
            .values_list('igname', flat=True)
        )
        print(f"How many duplicates? {len(duplicate_igname_list)}")
        if len(duplicate_igname_list) > 0:
            for igname in duplicate_igname_list:
                accounts = Account.objects.filter(igname=igname)
                indexes = []
                for account in accounts:
                    indexes.append(account.index)
                minimum_index = min(indexes)
                print(f"account to delete --------> {accounts.filter(index=minimum_index).last().igname}")
                accounts.filter(index=minimum_index).last().delete()
        else:
            print("No duplicates have been found in the system.")
        return Response({
            "handled":True
        }, status = status.HTTP_202_ACCEPTED)

    @action(detail=False,methods=['post'],url_path="create-with-account")
    def create_with_account(self, request):
        account = get_object_or_404(Account,id = request.data.pop('account_id'))
        print(request.data)
        print(account)
        thread = Thread.objects.create(**request.data,account=account)
        return Response({'id':thread.id}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="download-csv")
    def download_csv(self, request):
        date_format = "%Y-%m-%d %H:%M:%S"
        date_string = request.data.get('date')
        datetime_object = datetime.strptime(date_string, date_format)
        datetime_object_utc = datetime_object.replace(tzinfo=timezone.utc)
        threads = self.queryset.filter(created_at__gte=datetime_object_utc)
        accounts = []
        for thread in threads:
            account_logs = LogEntry.objects.filter(object_pk=thread.account.pk)
            for log in account_logs:
                if "index" in log.changes_dict.keys():
                    accounts.append({
                        "username": thread.account.igname,
                        "assigned_to": thread.account.assigned_to,
                        "current_stage": thread.account.index,
                        "date_outreach_began": thread.created_at,
                        "timestamp":log.timestamp,
                        **log.changes_dict
                        
                    })
        return Response(accounts, status=status.HTTP_200_OK)

    

    @action(detail=False, methods=["get"], url_path="response-rate")
    def response_rate(self, request):
        response_rate_object = []
        count = 0
        for thread in self.queryset:
            client_response = Message.objects.filter(
                Q(thread__thread_id=thread.thread_id) & Q(sent_by='Client')).order_by('-sent_on')
            if client_response.exists():
                count += 1
                response_rate_object.append(
                    {
                        "index": count,
                        "account": thread.account.igname,
                        "stage": thread.account.index
                    })
        return Response(data=response_rate_object, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="save-client-message")
    def save_client_message(self, request, pk=None):
        thread = self.get_object()

        last_message = Message.objects.filter(Q(thread__thread_id=thread.thread_id)
                                              & Q(sent_by='Client')).order_by('-sent_on').first()
        if request.data.get("text") != last_message.content:
            try:
                Message.objects.update_or_create(
                    content=request.data.get("text"),
                    sent_by="Client",
                    sent_on=timezone.now(),
                    thread=thread
                )
            except Exception as error:
                print(error)
        return Response({"success": True}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="save-salesrep-message")
    def save_salesrep_message(self, request, pk=None):
        thread = self.get_object()

        last_message = Message.objects.filter(Q(thread__thread_id=thread.thread_id)
                                              & Q(sent_by='Robot')).order_by('-sent_on').first()
        if request.data.get("text") != last_message.content:
            try:
                Message.objects.update_or_create(
                    content=request.data.get("text"),
                    sent_by="Robot",
                    sent_on=timezone.now(),
                    thread=thread
                )
            except Exception as error:
                print(error)
        return Response({"success": True}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="send-message-manually")
    def send_message_manually(self, request, pk=None):
        thread = self.get_object()

        serializer = SendManualMessageSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):

            account = thread.account
            salesrep = account.salesrep_set.last().ig_username
            data = {"message": serializer.data.get("message"), "username_to": account.igname, "username_from": salesrep}
            response = requests.post(settings.MQTT_BASE_URL+"/send-message", data=json.dumps(data))

            if response.status_code == 200:

                account.assigned_to = serializer.data.get("assigned_to")
                account.save()

                message = Message()
                message.content = serializer.data.get("message")
                message.sent_by = "Human"
                message.sent_on = timezone.now() #check:task we willl need to use correct timezone
                message.thread = thread
                message.save()

                thread.last_message_content = serializer.data.get("message")
                thread.last_message_at = timezone.now()
                thread.save()

                return Response(
                    {
                        "status": status.HTTP_200_OK,
                        "message": "Message sent successfully",
                        "thread_id": thread.thread_id,
                        "success": True,
                    }
                )
            else:
                return Response(
                    {
                        "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                        "message": "There was a problem sending your message",
                        "thread_id": thread.thread_id,
                        "success": True
                    }
                )
        else:
            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "message": serializer.errors(),
                    "thread_id": thread.thread_id,
                    "success": True
                }
            )

    def generate_response(self, request, *args, **kwargs):
        thread = Thread.objects.get(thread_id=kwargs.get('thread_id'))
        req = request.data
        query = req.get("message")

        account = Account.objects.get(id=thread.account.id)
        thread = Thread.objects.filter(account=account).last()

        client_messages = query.split("#*eb4*#")
        for client_message in client_messages:
            Message.objects.create(
                content=client_message,
                sent_by="Client",
                sent_on=timezone.now(),
                thread=thread
            )
        thread.last_message_content = client_messages[len(client_messages)-1]
        thread.unread_message_count = len(client_messages)
        thread.last_message_at = timezone.now()
        thread.save()

        if thread.account.assigned_to == "Robot":
            try:
                gpt_resp = get_gpt_response(account, str(client_messages), thread.thread_id)

                thread.last_message_content = gpt_resp
                thread.last_message_at = timezone.now()
                thread.save()

                result = gpt_resp
                Message.objects.create(
                    content=result,
                    sent_by="Robot",
                    sent_on=timezone.now(),
                    thread=thread
                )

                return Response(
                    {
                        "status": status.HTTP_200_OK,
                        "generated_comment": "".join(map(str, result)),
                        "text": request.data.get("message"),
                        "success": True,
                        "username": thread.account.igname,
                        "assigned_to": "Robot"
                    },
                    status=status.HTTP_200_OK,
                )

            except Exception as error:
                return Response(
                    {
                        "fulfillment_response": {
                            "messages": [
                                {
                                    "text": {
                                        "error": str(error),
                                    },
                                },
                            ]
                        }
                    },
                    status=status.HTTP_200_OK,
                )

        elif thread.account.assigned_to == 'Human':
            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "text": request.data.get("message"),
                    "success": True,
                    "username": thread.account.igname,
                    "assigned_to": "Human"

                }
            )

    def assign_operator(self, request, *args, **kwargs):
        try:
            thread = Thread.objects.get(thread_id=kwargs.get('thread_id'))
            account = get_object_or_404(Account, id=thread.account.id)
            account.assigned_to = request.data.get("assigned_to") if request.data.get('assigned_to') else 'Human'
            account.save()
        except Exception as error:
            print(error)

        try:
            subject = 'Hello Team'
            message = f'Please login to the system @https://booksy.us.boostedchat.com/ and respond to the following thread {account.igname}'
            from_email = 'lutherlunyamwi@gmail.com'
            recipient_list = ['lutherlunyamwi@gmail.com','tomek@boostedchat.com']
            send_mail(subject, message, from_email, recipient_list)
        except Exception as error:
            print(error)

        return Response(
            {
                "status": status.HTTP_200_OK,
                "assign_operator": True
            }

        )

    

    @action(detail=False, methods=["post"], url_path="save-external-messages")
    def save_external_messages(self, request, pk=None):
        
        account = None
        thread = None
        try:
            thread = Thread.objects.get(thread_id = request.data.get('thread_id'))
        except Thread.DoesNotExist:
            # create account object
            account = Account()
            account.igname = request.data.get('username')
            account.qualified = True
            account.save()

            # create thread object
            thread = Thread()
            thread.thread_id = request.data.get('thread_id')
            thread.account = account
            thread.save()

        # save message
        try:
            Message.objects.update_or_create(
                thread=thread,
                content=request.data.get("message"),
                sent_by="Client",
                sent_on=timezone.now()
            )
            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "save": True
                }

            )
        except Exception as error:
            logging.warning(error)
            return Response(
                {
                    "status": status.HTTP_200_OK,
                    "save": False
                }

            )

    @action(detail=True, methods=["get"], url_path="get-thread-messages")
    def get_thread_messages(self, request, pk=None):

        thread = self.get_object()
        messages = Message.objects.filter(thread=thread).order_by('sent_on')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="delete-all-thread-messages")
    def delete_thread_messages(self, request, pk=None):

        thread = self.get_object()
        Message.objects.filter(thread=thread).delete()
        return Response({"message": "Messages deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["post"], url_path="reset-thread-count")
    def reset_thread_count(self, request, pk=None):

        thread = self.get_object()
        thread.unread_message_count = 0
        thread.save()
        return Response({"message": "OK"}, status=status.HTTP_204_NO_CONTENT)
    

    def messages_by_ig_thread_id(self, request, *args, **kwargs):
        thread = Thread.objects.get(thread_id=kwargs.get('ig_thread_id'))
        messages = Message.objects.filter(thread=thread).order_by('sent_on')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    def thread_by_ig_thread_id(self, request, *args, **kwargs):
        thread = Thread.objects.get(thread_id=kwargs.get('ig_thread_id'))
        serializer = SingleThreadSerializer(thread)

        return Response(serializer.data)


    def has_client_responded(self, request, *args, **kwargs):
        username = request.data.get('username')
        thread = Thread.objects.filter(account__igname=username).last()
        client_messages = Message.objects.filter(Q(thread__thread_id=thread.thread_id) & Q(sent_by="Client")).order_by("-sent_on")
        
        if client_messages.exists():
            return Response({"has_responded":True}, status=status.HTTP_200_OK)
        else:
            return Response({"has_responded":False}, status=status.HTTP_200_OK)
        

class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def get_serializer_class(self):
        return self.serializer_class

    @action(detail=True, methods=["delete"], url_path="delete-message")
    def delete_message(self, request, pk=None):

        message = self.get_object()
        message.delete()
        return Response({"message": "Message deleted successfully"}, status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
def initialize_db(request):
    init_db()
    return Response({"message": "Db initialized successfully"})


@api_view(['POST'])
def update_thread_details(request):
    threads = Thread.objects.filter()
    for thread in threads:
        messages = Message.objects.filter(thread=thread).order_by("-sent_on")

        if len(messages) > 0:
            thread.unread_message_count = len(messages)
            thread.last_message_content = messages[0].content
            thread.last_message_at = messages[0].sent_on
            thread.save()

    return Response({"message": "Db initialized successfully"})
