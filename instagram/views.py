# Create your views here.
import csv
import io
import os
import logging
import uuid
import time
import json
import requests
import random
import pytz
from urllib.parse import urlparse
from auditlog.models import LogEntry
from celery.result import AsyncResult
from datetime import datetime, timezone as timezone2
from instagrapi.exceptions import UserNotFound
from rest_framework.views import APIView
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from lunyamwi.model_setup import setup_agent, setup_agent_workflow
from django.conf import settings
from django_celery_beat.models import PeriodicTask
from django.db.models import F,Value, Subquery, OuterRef
from django.db.models.functions import Coalesce
from django.utils.dateparse import parse_datetime


from base.helpers.push_id import PushID
from dialogflow.helpers.get_prompt_responses import get_gpt_response

from django_celery_beat.models import CrontabSchedule, PeriodicTask
from dialogflow.helpers.intents import detect_intent
from instagram.helpers.login import login_user
from sales_rep.models import SalesRep

from .utils import generate_time_slots

from .tasks import send_first_compliment,generate_response_automatic,reschedule, run_scheduler, delete_accounts,prequalify_task
from .helpers.init_db import init_db
from .models import Account, Comment, HashTag, Photo, Reel, Story, Thread, Video, Message, OutSourced,OutreachTime,AccountsClosed,Like,Comment,UnwantedAccount,StatusCheck
from .serializers import (
    AccountSerializer,
    OutSourcedSerializer,
    AddContentSerializer,
    HashTagSerializer,
    PhotoSerializer,
    ReelSerializer,
    SingleThreadSerializer,
    StorySerializer,
    ThreadSerializer,
    ThreadMessageSerializer,
    UploadSerializer,
    VideoSerializer,
    MessageSerializer,
    SendManualMessageSerializer,
    GetAccountSerializer,
    GetSingleAccountSerializer,
    ScheduleOutreachSerializer,
    LikeSerializer,
    CommentSerializer,
)
from django.db.models import Count, Case, When, IntegerField



class PaginationClass(PageNumberPagination):
    page_size = 100  # Set the number of items per page
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


class LikeViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    queryset = Like.objects.filter(account__isnull=False)
    serializer_class = LikeSerializer
    pagination_class = PaginationClass
    
    def create(self, request):   
        title = request.data.get('title')
        message = request.data.get('message')
        media_id =  request.data.get('media_id')
        collapse_key = request.data.get('collapse_key')
        optional_avatar_url = request.data.get('optional_avatar_url') 
        push_id =  request.data.get('push_id')
        push_category = request.data.get('push_category')
        intended_recipient_user_id = request.data.get('intended_recipient_user_id')
        source_user_id =  request.data.get('source_user_id')
        
        # Get or create account based on title
        try:
            account, created = Account.objects.get_or_create(igname=title)
        except Exception as error:
            print(error)

        # Create a new comment instance
        like_data = {
            'account': account.id,  # Use account ID for ForeignKey
            'message': message,
            'media_id': media_id,
            'collapseKey': collapse_key,
            'optionalAvatarUrl': optional_avatar_url,
            'pushId': push_id,
            'pushCategory': push_category,
            'intendedRecipientUserId': intended_recipient_user_id,
            'sourceUserId': source_user_id
        }

        # Initialize the serializer with the prepared data
        serializer = LikeSerializer(data=like_data)


        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, pk=None):
        paginator = self.pagination_class()
        queryset = Like.objects.all()
        result_page = paginator.paginate_queryset(queryset, request)  # Apply pagination
        likes = []
        
        for like in result_page:
            like_ = {
                "id": like.id,
                "deleted_at": like.deleted_at,
                "message": like.message,
                "media_id": like.media_id,
                "collapseKey": like.collapseKey,
                "optionalAvatarUrl": like.optionalAvatarUrl,
                "pushId": like.pushId,
                "pushCategory": like.pushCategory,
                "intendedRecipientUserId": like.intendedRecipientUserId,
                "sourceUserId": like.sourceUserId,
                "account": like.account.igname,
                "created_at": like.created_at
            }
            likes.append(like_)
        
        response_data = {
            'count': paginator.page.paginator.count,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'results': likes,
        }
        
        return Response(response_data,status=status.HTTP_200_OK)
    
class CommentViewSet(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    queryset = Comment.objects.filter(account__isnull=False)
    serializer_class = CommentSerializer
    pagination_class = PaginationClass

    def create(self, request):
        title = request.data.get('title')
        message = request.data.get('message')
        media_id = request.data.get('media_id')
        target_comment_id = request.data.get('target_comment_id')
        collapse_key = request.data.get('collapse_key')
        optional_avatar_url = request.data.get('optional_avatar_url')
        push_id = request.data.get('push_id')
        push_category = request.data.get('push_category')
        intended_recipient_user_id = request.data.get('intended_recipient_user_id')
        source_user_id = request.data.get('source_user_id')

        # Get or create account based on title
        try:
            account, created = Account.objects.get_or_create(igname=title)
        except Exception as error:
            print(error)

        # Create a new comment instance
        comment_data = {
            'account': account.id,  # Use account ID for ForeignKey
            'message': message,
            'media_id': media_id,
            'comment_id': target_comment_id,
            'target_comment_id': target_comment_id,
            'collapseKey': collapse_key,
            'optionalAvatarUrl': optional_avatar_url,
            'pushId': push_id,
            'pushCategory': push_category,
            'intendedRecipientUserId': intended_recipient_user_id,
            'sourceUserId': source_user_id
        }

        # Initialize the serializer with the prepared data
        serializer = CommentSerializer(data=comment_data)


        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, pk=None):
        paginator = self.pagination_class()
        queryset = Comment.objects.all()
        result_page = paginator.paginate_queryset(queryset, request)  # Apply pagination
        comments = []
        
        for comment in result_page:
            comment_ = {
                "id": comment.id,
                "comment_id": comment.comment_id,
                "message": comment.message,
                "media_id": comment.media_id,
                "target_comment_id": comment.target_comment_id,
                "collapseKey": comment.collapseKey,
                "optionalAvatarUrl": comment.optionalAvatarUrl,
                "pushId": comment.pushId,
                "pushCategory": comment.pushCategory,
                "intendedRecipientUserId": comment.intendedRecipientUserId,
                "sourceUserId": comment.sourceUserId,
                "account": comment.account.igname,
                "created_at":comment.created_at
            }
            comments.append(comment_)
        
        response_data = {
            'count': paginator.page.paginator.count,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'results': comments,
        }
        
        return Response(response_data,status=status.HTTP_200_OK)
    
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

    def list(self, request, pk=None):
        print(request)
        accounts = []
        paginator = self.pagination_class()
        status_param = request.GET.get('status_param')
        # status_param = request.GET.get('stage')
        search_query = request.GET.get("q")
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        created_at_gte = request.GET.get("created_at_gte")
        created_at_lt = request.GET.get("created_at_lt")
        qualified = request.GET.get("qualified")
        outreachSuccess = request.GET.get("outreach_success")
        
        if start_date:
            start_date = start_date.strip('"')
        if end_date:
            end_date = end_date.strip('"')
                    
        # start_date_parsed = parse_datetime(start_date ) if start_date else None
        start_date_parsed = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        # end_date_parsed = parse_datetime(end_date) if end_date else None
        end_date_parsed = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        
        if created_at_gte:
            created_at_gte_date = datetime.strptime(created_at_gte, '%Y-%m-%d').date() 
            # created_at_gte_parsed = timezone.make_aware(datetime.combine(created_at_gte_date, datetime.min.time()) + timezone.timedelta(hours=12))  # 12 PM UTC
            created_at_gte_parsed = created_at_gte_date
            
        else:
            created_at_gte_parsed = None
        # we have to add one day to the created_at_lt to get the correct date, because >= Today but less than tomorrow does not work
        
        if (created_at_gte is not None and created_at_lt is not None and created_at_lt == created_at_gte):
            # Account.objects.filter(created_at__gte=start_datetime, created_at__lte=end_datetime,qualified=True).count()
            created_at_gte_date = datetime.strptime(created_at_gte, '%Y-%m-%d').date() 
            created_at_gte_parsed = timezone.make_aware(datetime.combine(created_at_gte_date, datetime.min.time()))
            created_at_lt_parsed = timezone.make_aware(datetime.combine(created_at_gte_date, datetime.max.time()))
        else:
            if created_at_lt:
                created_at_lt_date =  datetime.strptime(created_at_lt, '%Y-%m-%d').date() + timezone.timedelta(days=1) if created_at_lt == created_at_gte else datetime.strptime(created_at_lt, '%Y-%m-%d').date() 
                created_at_lt_parsed = timezone.make_aware(datetime.combine(created_at_lt_date, datetime.min.time()) + timezone.timedelta(hours=12))  # 12 PM UTC
                # created_at_lt_parsed = timezone.make_aware(datetime.combine(created_at_lt_date, datetime.min.time()) + timezone.timedelta(hours=1))  # 11 PM UTC
            else: 
                created_at_lt_parsed = None
        
        
        
        queryset = Account.objects.filter(salesrep__isnull=False).annotate(
            last_message_at=F('thread__last_message_at'),
            # Get the latest sent_on from Message model related to the Thread
            last_message_sent_at= Subquery(
                    Message.objects.filter(thread=OuterRef('thread'))
                    .order_by('-sent_on')
                    .values('sent_on')[:1]
                ),
             # Get the sent_by field of the latest message
            last_message_sent_by=Subquery(
                Message.objects.filter(thread=OuterRef('thread'))
                .order_by('-sent_on')
                .values('sent_by')[:1]
            )
            ).annotate(
                # Coalesce to get the latest of either last_message_at or last_message_sent_at
                latest_message_at=Coalesce('last_message_sent_at', 'last_message_at', Value(datetime.min))
        ).order_by('-latest_message_at')  # Sort by the latest message, whichever comes first
   
        
        if start_date_parsed:
            print("gOT START DATE")
            if end_date_parsed:
                print("gOT end DATE")
                # Both dates are present
                #  messages = queryset.filter(last_message_at__gte=datetime(2024, 10, 7).date(), last_message_at__lte=datetime(2024, 11, 7).date())
                queryset = queryset.filter(
                    last_message_at__gte=start_date_parsed,
                    last_message_at__lte=end_date_parsed
                )
                # messages = queryset.filter(last_message_at__gte=datetime(2024, 10, 7).date(), last_message_at__lte=datetime(2024, 11, 7).date())
            else:
                # Only start_date is present; use it as both
                print(start_date)
                print(start_date_parsed)
                queryset = queryset.filter(
                    last_message_at__date=start_date_parsed.date() 
                )
        elif end_date_parsed:
            print(end_date_parsed)
            # If only end_date is present, you can decide how to handle it
            # queryset = queryset.filter(last_message_at__date=end_date_parsed.date())
        
        if status_param:
            if status_param.lower() == "null":
                # print("STATUS PARAM null")
                queryset = queryset.filter(status_param__isnull=True)
            elif status_param.lower() == "blank":
                # print("STATUS PARAM blank", status_param)
                queryset = queryset.filter(status_param="")
            else:
                queryset = queryset.filter(status_param=status_param.strip())
                # print(queryset.first.status_param)
                # print("After filter",queryset.count())
        if created_at_gte:
             #  messages = queryset.filter(last_message_at__gte=datetime(2024, 10, 7).date(), last_message_at__lte=datetime(2024, 11, 7).date())
                if created_at_lt:
                    queryset = queryset.filter(
                        created_at__gte= created_at_gte_parsed,
                        created_at__lte = created_at_lt_parsed
                    ).order_by('created_at')
                else:
                     queryset = queryset.filter(
                        created_at__gte= created_at_gte_parsed,
                        # created_at__lt = created_at_lt_parsed
                    ).order_by('created_at')
                    

        if qualified:
            queryset = queryset.filter(qualified=True) if qualified == "true" else queryset.filter(qualified=False) 
            
        if outreachSuccess:
            queryset = queryset.filter(outreach_success=True).order_by('created_at') if outreachSuccess == "true" else queryset.filter(outreach_success=False) 
            
        if search_query is not None:
            queryset = queryset.filter(igname__icontains=search_query.strip())
            
        result_page = paginator.paginate_queryset(queryset, request)  # Apply pagination
        
        for account in result_page:
            account_ = {
                "id": account.id,
                "assigned_to": account.assigned_to,
                "notes": account.notes,
                "created_at": account.created_at,
                "outreach_time": account.outreach_time,
                "outreach_success": account.outreach_success,
                "qualified": account.qualified,
                "confirmed_problems": account.confirmed_problems,
                "full_name": account.full_name or None,
                "igname": account.igname,
                "status": account.status.name if account.status else None,
                # "outreach": periodic_task.crontab.human_readable if periodic_task else "",
                "last_message_at": account.last_message_at,
                "last_message_sent_at": account.last_message_sent_at,
                "last_message_sent_by": account.last_message_sent_by,
                "stage": "Null" if account.status_param is None else ("Blank" if account.status_param == "" else account.status_param),


            }
            accounts.append(account_)

        response_data = {
            'count': paginator.page.paginator.count,
            'next': paginator.get_next_link(),
            'previous': paginator.get_previous_link(),
            'results': accounts,
        }
        return Response(response_data,status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'], url_path="clear-convo")
    def clear_convo(self, request, **kwargs):
        account = self.get_object()
        
        try:
            # reset status
            account.status = None
            account.status_param = 'Prequalified'
            account.assigned_to = 'Robot'
            account.save()
            thread = account.thread_set.latest('created_at')
            thread.message_set.clear()
        except Exception as error:
            return Response({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({"success": True, "message": "Conversations successfully reset"}, status=status.HTTP_200_OK)
        
    
    @action(detail=True, methods=['post'], url_path="add-notes")
    def add_notes(self, request, **kwargs):
        account = self.get_object()
        
        try:
            notes = request.data.get('notes')  # Extract 'notes' from the request data

            if not notes:
                return Response(
                    {"error": "Notes field is required."},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            account.notes = notes

            account.save()

        except Exception as error:
            return Response({"error": error}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(
            {"message": "Notes added successfully.", "notes": account.notes},
            status=status.HTTP_200_OK
        )    

    def retrieve(self, request, pk=None):
        queryset = Account.objects.all()
        user = get_object_or_404(queryset, pk=pk)
        serializer = GetSingleAccountSerializer(user)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path="active-stages")
    def active_stages(self, request):
        # Retrieve all unique status_param values
        unique_status_params = Account.objects.values_list('status_param', flat=True).distinct()
        
        # Return as an array
        return Response(list(unique_status_params), status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path="active-stage-stats")
    def active_stage_stats(self, request):
        # We'll add this filers as soon as we know when they moved from one stage to the next
        # start_date = request.GET.get("start_date")
        # end_date = request.GET.get("end_date")
        
        # if start_date:
        #     start_date = start_date.strip('"')
        # if end_date:
        #     end_date = end_date.strip('"')
        
        # start_date_parsed = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        # end_date_parsed = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        
        stages_with_counts = Account.objects.values('status_param') \
            .annotate(total_accounts=Count('status_param')) \
            .annotate(
                custom_order=Case(
                    When(status_param='Prequalified', then=0),
                    When(status_param='Sales Qualified', then=1),
                    When(status_param='Committed', then=2),
                    output_field=IntegerField()
                )
            )\
            .order_by('custom_order')
            
            # Fetch the counts for the specific transitions between stages based on the assumption
        prequalified_to_sales_qualified_count = Account.objects.filter(status_param='Sales Qualified').count()
        sales_qualified_to_committed_count = Account.objects.filter(status_param='Committed').count()

        # Calculate the total number of accounts in each stage
        prequalified_count = Account.objects.filter(status_param='Prequalified').count()
        sales_qualified_count = Account.objects.filter(status_param='Sales Qualified').count()

         # Calculate the percentages
        percentage_prequalified_to_sales_qualified = (prequalified_to_sales_qualified_count / prequalified_count * 100) if prequalified_count > 0 else 0
        percentage_sales_qualified_to_committed = (sales_qualified_to_committed_count / sales_qualified_count * 100) if sales_qualified_count > 0 else 0

        # Add the transition counts and percentages to the corresponding stages
        for stage in stages_with_counts:
            if stage['status_param'] == 'Committed':
                stage['sales_qualified_to_committed_count'] = sales_qualified_to_committed_count
                stage['percentage_sales_qualified_to_committed'] = percentage_sales_qualified_to_committed
            elif stage['status_param'] == 'Sales Qualified':
                stage['prequalified_to_sales_qualified_count'] = prequalified_to_sales_qualified_count
                stage['percentage_prequalified_to_sales_qualified'] = percentage_prequalified_to_sales_qualified

    
        # Return the results as a list of dictionaries
        return Response(stages_with_counts, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def threads_with_messages(self, request, pk=None):
        """
        Retrieve all threads related to a specific account along with their messages,
        sorted by sent_on in descending order within each thread.
        """

        try:
            account = self.get_object()  # Get the account based on the pk
            threads = Thread.objects.filter(account=account).order_by('-last_message_at')  # Optionally order threads

            # Serialize the threads with nested messages
            serialized_data = ThreadMessageSerializer(threads, many=True).data
            account_serializer = GetSingleAccountSerializer(account).data

            return Response({
                'id': account.id,
                'igname': account.igname,
                'account': account_serializer,
                'threads': serialized_data
            })

        except Account.DoesNotExist:
            return Response({"error": "Account not found"}, status=404)
    
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

    @action(detail=False,methods=["post"],url_path="get-id")
    def get_id(self,request,pk=None):
        username = request.data.get("username")
        account = Account.objects.filter(igname = username).latest('created_at')
        if account.outsourced_set.exists():
            return Response(
                {
                    "id": account.id,
                    "outsourced_id": account.outsourced_set.latest('created_at').id,
                    "qualified": account.qualified
                }
            )
        else:
            return Response(
                {
                    "id": account.id,
                    "qualified": account.qualified
                }
            )


    @action(detail=False,methods=['post'],url_path='qualify-account')
    def qualify_account(self, request, pk=None):
        account = Account.objects.filter(igname = request.data.get('username')).latest('created_at')
        accounts_qualified = []
        if account.outsourced_set.exists():
            account.qualified = request.data.get('qualify_flag')
            account.relevant_information = request.data.get("relevant_information")
            account.scraped = True
            account.save()
            accounts_qualified.append(
                {
                    "qualified":account.qualified,
                    "account_id":account.id
                }
            )
    
        return Response(accounts_qualified, status=status.HTTP_200_OK)
    

    @action(detail=False,methods=['post'],url_path='manually-trigger')
    def manually_trigger(self, request, pk=None):
        account = Account.objects.filter(igname = request.data.get('username')).latest('created_at')
        accounts_triggered = []
        if account.outsourced_set.exists():
            account.is_manually_triggered = True
            account.save()
            accounts_triggered.append(
                {
                    "manually_triggered":account.is_manually_triggered,
                    "account_id":account.id
                }
            )
    
        return Response(accounts_triggered, status=status.HTTP_200_OK)

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
        # There could be more than one thread with the same thread id
        # thread = Thread.objects.get(thread_id=kwargs.get('ig_thread_id')) 
        thread = Thread.objects.filter(thread_id=kwargs.get('ig_thread_id')).first() 
        if thread.account:
            accounts = Account.objects.filter(id=thread.account.id)
            account = accounts.latest('created_at')
            serializer = GetSingleAccountSerializer(account)
            return Response(serializer.data)
        else:
            return Response({"error":"Account does not have thread attached"})
    
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

    @action(detail=False, methods=["get"], url_path="get-connected-accounts")
    def get_connected_accounts(self, request, pk=None):
        response = requests.get(settings.MQTT_BASE_URL+"/accounts/connected")
        print(response.status_code)
        
        if response.status_code == 200:
            print(json.loads(response.content))
            print(response.json)
            
            return Response(
                    {
                        "status": status.HTTP_200_OK,
                        "mqtt_running": True,
                        "mqtt_connected": True,
                        "connected_accounts": json.loads(response.content),
                        "success": True,
                    }
                )
        else:
            return Response(
                    {
                        "status": response.status_code,
                        "mqtt_running": False,
                        "mqtt_connected": False,
                        "connected_accounts": [],
                        "success": True,
                    }
                )
            
    @action(detail=False, methods=["get"], url_path="get-loggedin-accounts")
    def get_loggedin_accounts(self, request, pk=None):
        response = requests.get(settings.MQTT_BASE_URL+"/accounts/loggedin")
        
        if response.status_code == 200:
            
            return Response(
                    {
                        "status": status.HTTP_200_OK,
                        "mqtt_running": True,
                        "mqtt_connected": True,
                        "connected_accounts": json.loads(response.content),
                        "success": True,
                    }
                )
        else:
            return Response(
                    {
                        "status": response.status_code,
                        "mqtt_running": False,
                        "mqtt_connected": False,
                        "connected_accounts": [],
                        "success": True,
                    }
                )
            
    @action(detail=False, methods=["get"], url_path="check-mqtt-health")
    def get_mqtt_heath(self, request, pk=None):
        response = requests.get(settings.MQTT_BASE_URL+"/health")
        
        if response.status_code == 200:
             return Response(
                    {
                        "status": status.HTTP_200_OK,
                        "mqtt_running": True,
                        "mqtt_connected": True,
                        "success": True,
                    }
                )
        else:
            return Response(
                    {
                        "status": response.status_code,
                        "mqtt_running": False,
                        "mqtt_connected": False,
                        "success": True,
                    }
                )
            
    @action(detail=False, methods=["get"], url_path="get-comments")
    def get_mqtt_comments(self, request, pk=None):
        status_param = request.GET.get('username')
        media_id = request.GET.get('media_id')
        data = {"username_from": 'denn_mokaya', "media_id": '1263679849772992148'}
        response = requests.post(settings.MQTT_BASE_URL+"/fetchComments", data=json.dumps(data))
        print("hdhdhdh")
        if response.status_code == 200:
             return Response(
                    {
                        "status": status.HTTP_200_OK,
                        "data": json.loads(response.content),
                        "success": True,
                    }
                )
        else:
            return Response(
                    {
                        "status": response.status_code,
                        "data": [],
                        "success": False,
                    }
                )
            
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
            delete_accounts.delay(duplicate_igname_list)
        else:
            print("No duplicates have been found in the system.")
        return Response({
            "handled":True,
            "found": len(duplicate_igname_list)
        }, status = status.HTTP_202_ACCEPTED)
    
    @action(detail=False, methods=["post"], url_path="qualify-test-accounts")
    def qualify_test_accounts(self, request):
        # test_account = Account.objects.filter(igname__icontains=request.data.get("igname")).latest('created_at')
        try:
            test_account = Account.objects.filter(igname__icontains=request.data.get("igname")).latest('created_at')
        except Account.DoesNotExist:
            return Response({"error": "No matching test account found."}, status=status.HTTP_404_NOT_FOUND)

        try:
            UnwantedAccount.objects.filter(username__icontains=test_account.igname).delete()
        except Exception as error:
            return Response({"error": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        try:
            # reset lead
            test_account.qualified = True
            test_account.created_at = timezone.now()
            test_account.status = None
            test_account.status_param = 'Prequalified'
            test_account.assigned_to = 'Robot'
            test_account.save()
            if test_account.thread_set.exists():
                thread = test_account.thread_set.latest('created_at')
                thread.message_set.clear()
        except Exception as error:
            return Response({"error": str(error)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response({"status": status.HTTP_200_OK, "message": "Test account successfully qualified."})

    @action(detail=False,methods=['post'],url_path='prequalify-accounts')
    def prequalify_accounts(self, request, pk=None):
        prequalify_task.delay() 
        
        return Response({"message":"Succesfully qualified accounts"}, status=status.HTTP_200_OK)

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
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        paginator = self.pagination_class()
       
        if start_date:
            start_date = start_date.strip('"')
        if end_date:
            end_date = end_date.strip('"')
    
        start_date_parsed = parse_datetime(start_date ) if start_date else None
        end_date_parsed = parse_datetime(end_date) if end_date else None
        
       
        print("8888888888888888888")
        print(start_date)
        print(start_date_parsed)
        queryset = Thread.objects.select_related('account').filter(account__salesrep__isnull=False).annotate(last_message_at_ordering=Coalesce('last_message_at', Value(datetime.min))).order_by(F('last_message_at_ordering').desc())
        message_data = []
        messages = None
          # Apply date range filter if both start_date and end_date are provided
        # if start_date and end_date:
        #     try:
        #         # Parse the dates and filter the queryset
        #         start_date_parsed = parse_date(start_date)
        #         end_date_parsed = parse_date(end_date)
        #         if start_date_parsed and end_date_parsed:
        #             queryset = queryset.filter(
        #                 last_message_at__gte=start_date_parsed,
        #                 last_message_at__lte=end_date_parsed
        #                 )
        #     except ValueError:
        #         pass  
         # Use start_date as both start and end if only start_date is provided
        if start_date_parsed:
            if end_date_parsed:
                # Both dates are present
                queryset = queryset.filter(
                    last_message_at__gte=start_date_parsed,
                    last_message_at__lte=end_date_parsed
                )
            else:
                # Only start_date is present; use it as both
                print("kkkkkkkkkkkkkkkkkkkkkkk")
                print(start_date)
                print(start_date_parsed)
                queryset = queryset.filter(
                    last_message_at__date=start_date_parsed.date() 
                )
        elif end_date_parsed:
            # If only end_date is present, you can decide how to handle it
            queryset = queryset.filter(last_message_at__date=end_date_parsed.date())


        # Show only threads that have sales reps & order by last_message_at    
       

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
                accounts = Account.objects.filter(igname=igname).order_by('-created_at')
                accounts_to_delete = accounts[1:]  # Keep the latest one, delete the rest
                delete_count = Account.objects.filter(id__in=[acc.id for acc in accounts_to_delete]).delete()
                print(f"Deleted {delete_count} duplicate(s) for igname: {igname}")
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

        # check if the message is already saved
        last_message = Message.objects.filter(Q(thread__thread_id=thread.thread_id)
                                              & Q(sent_by='Client')).order_by('-sent_on').first()
        if request.data.get("text") != last_message.content:
            try:
                # Save client message from here
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
  
    @action(detail=False, methods=["post"], url_path="sync-messages")
    def sync_messages(self, request, *args, **kwargs):
        # Get data from request
        thread_id = request.data.get("threadId")
        messages = request.data.get('messages')
        igname = request.data.get('igname')
        number_of_messages_prior = Message.objects.count()
        
        if not thread_id or not messages:
            return Response({"error": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Find the thread
            thread = Thread.objects.get(thread_id=thread_id)
            print("Thread FOUND!")
        except Thread.DoesNotExist:
            # check if any message here includes the influecer
            # if so create the thread and save the messages 
            # if not skip this guy
            print("Thread NOT FOUND! creating ONE")
            accounts = Account.objects.filter(igname=igname)
            account = None
            # check if account exists
            if accounts.exists():
                account = accounts.latest('created_at')
                print("ACCOUNT EXISTS!")
            # else: # if not create one
            #     account = Account()
            #     account.igname = igname
            #     account.created_at = timezone.now() - timezone.timedelta(days=5)
            #     account.qualified = True
            #     account.scraped = True
            #     account.status = StatusCheck.objects.get(name="sent_compliment")
            #     account.relevant_information = {"username":igname}
            #     account.save()
            #     try: # generate new outsourced information for it
            #         OutSourced.objects.create(results={"username":igname},account=account)
            #     except Exception as err:
            #         logging.warning(err)

                

            if account:
                print("LEAD EXISTS CREATING A NEW THREAD!")
                thread = Thread()
                thread.thread_id = thread_id
                thread.account = account
                thread.save()
                print("Thread CREATED A NEW THREAD!")
            else:
                return Response({"error": "LEAD DOES NOT EXIST"}, status=status.HTTP_404_NOT_FOUND)

        try:
        # Iterate through the messages
            for message in  messages:
                user_id = message.get("userId")
                content = message.get("content")
                message_id = message.get("messageId")
                timestamp = message.get("timestamp")
                content_data = message.get("contentData")
                content_type = message.get("itemType")
                
                # Convert microseconds to seconds
                timestamp_seconds = int(timestamp) / 1_000_000

                # Create a datetime object from the timestamp
                formatted_time = datetime.fromtimestamp(timestamp_seconds, tz=timezone2.utc)
                # datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)


                # Skip if any critical information is missing
                if not user_id or not content or not message_id or not timestamp:
                    print(f"Skipping message with incomplete data: {message}")
                    continue

                # Check if the message already exists
                if user_id == 'client':
                    existing_message = Message.objects.filter(sent_by="Client", thread=thread, content=content).first()
                    if existing_message:
                        # we can update the message id
                        print(f"Message already exists: {message_id}", content_data)
                        existing_message.message_id = message_id
                        existing_message.content_data = content_data
                        existing_message.content_type = content_type
                        existing_message.save()
                        continue

                    # Create the message
                    Message.objects.create(
                        thread=thread,
                        sent_by="Client",
                        # user_id=user_id,
                        content=content,
                        message_id=message_id,
                        sent_on=formatted_time,
                        content_type = content_type,
                        content_data = content_data,
                    )
                    
                    print(f"Client Message created: {message_id}")
                else:
                    existing_message = Message.objects.filter(sent_by="Robot", thread=thread, content=content).first()
                    if existing_message:
                        # we can update the message id
                        print(f"Message already exists: {message_id}")
                        existing_message.message_id = message_id
                        content_type = content_type,
                        content_data = content_data,
                        existing_message.save()
                        continue

                    # Create the message
                    Message.objects.create(
                        thread=thread,
                        sent_by="Robot",
                        # user_id=user_id,
                        content=content,
                        message_id=message_id,
                        sent_on=formatted_time,
                        content_type=content_type,
                        content_data=content_data
                    )
                    
                    print(f"Influener Message created: {message_id}")
            if Message.objects.count() > number_of_messages_prior:
                try:
                    subject = 'Hello Team'
                    message = f'Hooray! New messages have been synced. {Message.objects.count() - number_of_messages_prior} new messages have been added to the database.'
                    from_email = 'lutherlunyamwi@gmail.com'
                    recipient_list = ['dennorina@gmail.com','lutherlunyamwi@gmail.com','tomek@boostedchat.com']
                    send_mail(subject, message, from_email, recipient_list)
                except Exception as error:
                    logging.warning(error)

                return Response({"success": True}, status=status.HTTP_201_CREATED)
                
            else:
                return Response({"message": "No new messages"}, status=status.HTTP_201_CREATED)
            
        except Exception as e:  
            return Response({"success": False, "message": e}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def generate_outreach_times(self, request, *args,**kwargs):
        start_time = request.data.get("start_time")
        end_time = requests.data.get("end_time")
        slots = request.data.get("slots")
        time_slots = generate_time_slots(start_time, end_time, slots)
        # make it dynamic
        for time_slot in time_slots:
            try:
                OutreachTime.objects.update_or_create(time_slot)
            except Exception as err:
                print(err)
            print(time_slot)
        return Response({"message":"time slots successfully generated"})

        
    def check_account_exists(self,request,*args,**kwargs):
        account = Account.objects.filter(igname = request.data.get('username'))
        if account.exists():
            return Response({"exists":True})
        else:
            return Response({"exists":False})
        
    def check_thread_exists(self,request,*args,**kwargs):
        account = Account.objects.filter(igname = request.data.get('username')).latest('created_at')
        if account.thread_set.exists():
            return Response({"exists":True})
        else:
            return Response({"exists":False})

    
    def is_time_slot_within_window(self, time_slot):
        # Set the Miami timezone (UTC-4)
        miami_tz = pytz.timezone('US/Eastern')  # Adjusts for DST
        
        # Convert time_slot to Miami timezone if it's not already
        if time_slot.tzinfo != miami_tz:
            time_slot = time_slot.astimezone(miami_tz)
        
        # Define the desired time window in Miami time
        start_time = time_slot.replace(hour=7, minute=0, second=0, microsecond=0)
        end_time = time_slot.replace(hour=20, minute=59, second=0, microsecond=0)
        
        # Check if time_slot is within the window
        return start_time <= time_slot <= end_time


    def get_qualified_threads_and_respond(self, request, *args, **kwargs):
        
        # Get the start of yesterday's date
        yesterday = timezone.now().date() - timezone.timedelta(days=1)
        tomorrow = timezone.now().date() + timezone.timedelta(days=1)
        yesterday_start = timezone.make_aware(timezone.datetime.combine(yesterday, timezone.datetime.min.time()))
        unwanted_usernames = UnwantedAccount.objects.values_list('username', flat=True)

        # Filter accounts that are qualified and created from yesterday onwards, and exclude accounts that are not wanted
        accounts = Account.objects.filter(
            Q(qualified=True) & Q(created_at__gte=yesterday_start) & Q(created_at__lte=tomorrow)
        ).exclude(
            status__name="sent_compliment"
        ).exclude(
            igname__in=unwanted_usernames
        ) 
        account_messages_sent = []
        
        if accounts.exists():
            for i,account in enumerate(accounts):
                # if account.salesrep_set.exists(): # if they are assigned a salesrep
                    threads = Thread.objects.filter(account=account)  
                    if threads.exists():
                        for thread in threads:  
                            client_messages = Message.objects.filter(Q(thread__thread_id=thread.thread_id) & Q(sent_by="Client")).order_by("-sent_on")
                            robot_messages = Message.objects.filter(Q(thread__thread_id=thread.thread_id) & Q(sent_by="Robot")).order_by("-sent_on")
                            if client_messages.count() > 0 and robot_messages.count() == 0:
                                print("outbound sales")
                                # import pdb;pdb.set_trace()
                                time_slots = OutreachTime.objects.filter(time_slot__gte=timezone.now()).order_by('time_slot')
                                try:
                                    schedule = None
                                    # set a window to which it cannot by pass
                                    
                                    time_slot = timezone.now()+timezone.timedelta(hours=i/2)
                                    if self.is_time_slot_within_window(time_slot):
                                        send_first_compliment.apply_async(args=[[account.igname],thread.last_message_content], eta=time_slot)
                                        try:
                                            account.outreach_time = time_slot
                                            account.save()
                                        except Exception as error:
                                            logging.warning(f"Failed to save outreach time - {error}")
                                    # run_scheduler.delay(target_time=time_slot,username=account.igname,message=thread.last_message_content)
                                        
                                        
                                    
                                    # send_first_compliment.delay(username=account.igname,message=thread.last_message_content)
                                except Exception as err:
                                    print(err)
                    else:
                        print("inbound sales")
                        # import pdb;pdb.set_trace()
                        time_slots = OutreachTime.objects.filter(time_slot__gte=timezone.now()).order_by('time_slot')
                        try:
                            time_slot = timezone.now()+timezone.timedelta(hours=i/2)
                            # run_scheduler.delay(target_time=time_slot,username=account.igname,message="")
                            # time_slot = timezone.now()+timezone.timedelta(hours=i/2)
                            if self.is_time_slot_within_window(time_slot):
                                send_first_compliment.apply_async(args=[[account.igname],""], eta=time_slot)

                                try:
                                    account.outreach_time = time_slot
                                    account.save()
                                except Exception as error:
                                    logging.warning(f"Failed to save outreach time - {error}")

                            # send_first_compliment.delay(username=account.igname,message="")
                            # send_first_compliment.delay(username=account.igname,message=thread.last_message_content)
                        except Exception as err:
                            print(err)
            return Response({'message':'succesfully scheduled reponses'},status=status.HTTP_200_OK)
        else:
            return Response({'message': 'accounts do not exist'})


    def generate_followup_response(self, request, *args, **kwargs):
        date_threshold = timezone.now() - timezone.timedelta(days=30)
        last_message_subquery = (
            Message.objects
            .filter(thread=OuterRef('thread'))
            .order_by('-sent_on')
        )
        latest_accounts_subquery = (
            Account.objects
            .filter(igname=OuterRef('igname'))  # Match the igname of the outer query
            .order_by('-created_at')  # Order by created_at descending
        )
        users_without_responses = (
            Account.objects
            .filter(
                qualified=True,
                question_asked=False,
                status__name='sent_compliment',
                created_at__gte=date_threshold  # Filter for accounts created in the last 30 days
            )
            .annotate(client_message_count=Count(
                'thread__message',
                filter=Q(thread__message__sent_by='Client')
            ))
            .annotate(last_message_sent_by_robot=Subquery(
                last_message_subquery.values('sent_by')[:1]  # Get the 'sent_by' field of the last message
            ))
            .filter(
                Q(client_message_count__gt=0) |  # Include users with client messages
                Q(last_message_sent_by_robot='Robot')  # Or where the last message was sent by Robot
            )
            .filter(
                created_at=Subquery(latest_accounts_subquery.values('created_at')[:1])  # Ensure we only get the latest account per igname
            )
            .values_list('igname', flat=True)
        )
        users_without_responses_list = list(users_without_responses)  # Convert queryset to list
        num_users = len(users_without_responses_list)
        random_users = None

        # If there are fewer than 10 users, slice accordingly
        if num_users > 10:
            random_users = random.sample(users_without_responses_list[:num_users - 10], min(3, num_users - 10))
        else:
            random_users = random.sample(users_without_responses_list, min(3, num_users))
        
        for username in random_users:
            account = Account.objects.filter(igname=username).latest('created_at')
            account.question_asked = True
            account.save()
            if account.thread_set.exists():
                thread = account.thread_set.latest('created_at')

                generate_response_endpoint = f"https://api.booksy.us.boostedchat.com/v1/instagram/dflow/{thread.thread_id}/generate-response/"
                
                try:
                    data = {"message": ""}
                    response = requests.post(generate_response_endpoint, json=data)  # Use json parameter for proper content-type
                    
                    if response.status_code in [200, 201]:
                        task_id = response.json()['task_id']
                        if task_id:
                            # Polling for task completion
                            celery_url = f"https://api.booksy.us.boostedchat.com/v1/instagram/celery-task-status/{task_id}/"
                            while True:
                                celery_response = requests.get(celery_url)

                                if celery_response.status_code == 200:
                                    print(f"Async Response: {celery_response.json()}")
                                    
                                    
                                    task_status = celery_response.json()['state']
                                    print(f"Status: {task_status}")
                                    if task_status == 'SUCCESS':
                                        message = celery_response.json()['result']['generated_comment']
                                        salesrep = SalesRep.objects.filter(available=True).latest('created_at')
                                        text_data = {
                                            "message": message,
                                            "username_to": account.igname,
                                            "username_from": salesrep.ig_username
                                        }
                                        text_response = requests.post(settings.MQTT_BASE_URL + "/send-message", json=text_data)
                                        if text_response.status_code == 200:
                                            print(f"Message sent to {account.igname}")
                                            time.sleep(100)  # Wait before sending the next message
                                        break  # Exit loop after successful message sending
                                    elif task_status == 'FAILURE':
                                        print(f"Task {task_id} failed.")
                                        break  # Exit loop on failure
                                else:
                                    print(f"Failed to get task status: {celery_response.status_code}")
                                
                                time.sleep(10)  # Wait before polling again (adjust as necessary)

                except Exception as err:
                    print(err)
            else:
                print(f"No thread found for {username}")

        return Response({"message": "Followup responses generated successfully"}, status=status.HTTP_200_OK)

    
    def generate_response(self, request, *args, **kwargs):
        thread = Thread.objects.filter(thread_id=kwargs.get('thread_id')).latest('created_at')
        req = request.data
        query = req.get("message")
        print(query)
        result = generate_response_automatic.delay(query, thread.thread_id)
        # import pdb;pdb.set_trace()
        print(result.id)

        return Response({
            "status": status.HTTP_200_OK,
            "message": "Task started successfully",
            "task_id": result.id
        }, status=status.HTTP_200_OK)
    
    def celery_task_status(self, request, task_id,*args,**kwargs):
        result = AsyncResult(task_id)
        print(result)
        
        return Response({
            'task_id': task_id,
            'state': result.state,
            'result': result.result if result.state == 'SUCCESS' else None,
        })

    def assign_operator(self, request, *args, **kwargs):
        try:
            thread = Thread.objects.filter(account__igname=kwargs.get('username')).latest('created_at')
            account = get_object_or_404(Account, id=thread.account.id)
            account.assigned_to = request.data.get("assigned_to") if request.data.get('assigned_to') else 'Human'
            account.save()
            try:
                subject = 'Hello Team'
                message = f'Please login to the system @https://booksy.us.boostedchat.com/ and respond to the following thread {account.igname}'
                from_email = 'lutherlunyamwi@gmail.com'
                recipient_list = ['lutherlunyamwi@gmail.com','tomek@boostedchat.com']
                send_mail(subject, message, from_email, recipient_list)
            except Exception as error:
                print(error)
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
        # There come more than one threads with the same id
        # thread = Thread.objects.get(thread_id=kwargs.get('ig_thread_id'))
        thread = Thread.objects.filter(thread_id=kwargs.get('ig_thread_id')).first() 
        messages = Message.objects.filter(thread=thread).order_by('sent_on')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)

    def thread_by_ig_thread_id(self, request, *args, **kwargs):
        # There come more than one threads with the same id
        # thread = Thread.objects.get(thread_id=kwargs.get('ig_thread_id'))
        thread = Thread.objects.filter(thread_id=kwargs.get('ig_thread_id')).first() 
        serializer = SingleThreadSerializer(thread)

        return Response(serializer.data)

    
    def has_client_responded(self, request, *args, **kwargs):
        date_threshold = timezone.now() - timezone.timedelta(days=30)
        last_message_subquery = (
            Message.objects
            .filter(thread=OuterRef('thread'))
            .order_by('-sent_on')
        )
        latest_accounts_subquery = (
            Account.objects
            .filter(igname=OuterRef('igname'))  # Match the igname of the outer query
            .order_by('-created_at')  # Order by created_at descending
        )
        users_without_responses = (
            Account.objects
            .filter(
                qualified=True,
                question_asked=False,
                status__name='sent_compliment',
                created_at__gte=date_threshold  # Filter for accounts created in the last 30 days
            )
            .annotate(client_message_count=Count(
                'thread__message',
                filter=Q(thread__message__sent_by='Client')
            ))
            .annotate(last_message_sent_by_robot=Subquery(
                last_message_subquery.values('sent_by')[:1]  # Get the 'sent_by' field of the last message
            ))
            .filter(
                Q(client_message_count__gt=0) |  # Include users with client messages
                Q(last_message_sent_by_robot='Robot')  # Or where the last message was sent by Robot
            )
            .filter(
                created_at=Subquery(latest_accounts_subquery.values('created_at')[:1])  # Ensure we only get the latest account per igname
            )
            .values_list('igname', flat=True)
        )

        if len(users_without_responses) == 0:
            return Response({"has_responded":True}, status=status.HTTP_200_OK)
        elif len(users_without_responses) > 0:
            return Response({"has_responded":False}, status=status.HTTP_200_OK)
    

    def webhook(self,request,*args,**kwargs):
        data = None
        try:
            data = request.data
            print(data)
        except Exception as err:
            print(err)
            try:
                data = json.loads(request.body)
                print(data)
            except Exception as err:
                print(err)
                try:
                    data = request.json()
                except Exception as err:
                    print(err)
                    try:
                        data = json.loads(request.body.decode('utf-8'))
                    except  Exception as err:
                        print(err)
        
        try:
            closed = AccountsClosed()
            closed.data = data
            closed.save()
        except Exception as err:
            print(err,'was unable to save data')
                    
        return Response({"message":"webhook received"})
        

class Reschedule(APIView):
    def post(self, request, *args, **kwargs):
        reschedule.delay()

        print("Tasks have been scheduled successfully.")
    
        return Response({"message":"Tasks have been scheduled successfully."})



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
