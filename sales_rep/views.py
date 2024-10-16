import json
import logging

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_celery_beat.models import CrontabSchedule, PeriodicTask
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from authentication.models import User
from data.helpers.random_data import get_random_compliment
from instagram.helpers.llm import query_gpt
from instagram.helpers.login import login_user
from instagram.models import Account, StatusCheck
from instagram.tasks import send_first_compliment

from .helpers.task_allocation import no_consecutives, no_more_than_x
from .models import SalesRep
from .serializers import AccountAssignmentSerializer, SalesRepSerializer

# Create your views here.


class SalesRepManager(viewsets.ModelViewSet):
    queryset = SalesRep.objects.all()
    serializer_class = SalesRepSerializer

    def get_serializer_class(self):
        if self.action == "assign_accounts":
            return AccountAssignmentSerializer

        return self.serializer_class

    def list(self, request):

        reps = SalesRep.objects.filter(available=True)
        user_info = []
        for rep in reps:
            if User.objects.filter(id=rep.user.id).exists():
                info = {"user": User.objects.filter(id=rep.user.id).values(), "instagram": rep.instagram.values(),
                        "ig_username": rep.ig_username, "ig_password": rep.ig_password, "country": rep.country, "city": rep.city}
                user_info.append(info)

        response = {"status_code": status.HTTP_200_OK, "info": user_info}
        return Response(response, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="all")
    def get_all_flattened(self, request, pk=None):
        sales_reps = SalesRep.objects.all()
        serializer = SalesRepSerializer(sales_reps, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="reassign")
    def reassign_salesrep(self, request, pk=None):
        salesrep = self.get_object()
        new_salesrep_id = request.data.get('new_salesrep_id')  

        try:
            new_salesrep = SalesRep.objects.get(id=new_salesrep_id)
        except SalesRep.DoesNotExist:
            return Response({"error": "New salesrep not found"}, status=status.HTTP_404_NOT_FOUND)

        # Reassign the salesrep
        salesrep.salesrep_field = new_salesrep  # Replace "salesrep_field" with the actual field in your SalesRep model
        salesrep.save()

        return Response({"success":True}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="assign-accounts")
    def assign_accounts(self, request, pk=None):
        serializer = AccountAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            account = Account.objects.get(igname="sdbatory")
        except:
            return Response({"message": "Account does not exist"}, status=status.HTTP_400_BAD_REQUEST)

        sales_rep = SalesRep.objects.filter(ig_username='mike_bsky').last()
        sales_rep.instagram.add(account)
        try:
            schedule, _ = CrontabSchedule.objects.get_or_create(
                minute="*/3",
                hour="*",
                day_of_week="*",
                day_of_month="*",
                month_of_year="*",
            )
        except Exception as error:
            logging.warning(str(error))

        try:
            task, _ = PeriodicTask.objects.get_or_create(
                name=f"SendFirstCompliment-{account.igname}",
                crontab=schedule,
                task="instagram.tasks.send_first_compliment",
                args=json.dumps([[account.igname]])
            )
        except Exception as error:
            logging.warning(str(error))

        return Response({"accounts": "Set"})
