import math
import random

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

        reps = SalesRep.objects.all()
        user_info = []
        for rep in reps:
            if User.objects.filter(id=rep.user.id).exists():
                info = {"user": User.objects.filter(id=rep.user.id).values(), "instagram": rep.instagram.values()}
                user_info.append(info)

        response = {"status_code": status.HTTP_200_OK, "info": user_info}
        return Response(response, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="assign-accounts")
    def assign_accounts(self, request, pk=None):
        serializer = AccountAssignmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instagram_accounts_ = []
        accounts = Account.objects.filter(Q(status=None) | ~Q(status__name="sent_first_compliment"))
        if accounts.exists():
            instagram_accounts_.append(accounts)

        print(accounts)
        instagram_accounts = []
        for accounts_ in instagram_accounts_:
            for account in accounts_:
                instagram_accounts.append(account.id)

        salesreps = list(SalesRep.objects.all())

        if len(salesreps) == 0:
            return Response({"message": "No sales reps"}, status=status.HTTP_400_BAD_REQUEST)

        ration = math.ceil(len(instagram_accounts) / len(salesreps))

        i = 0
        accounts_complimented = []

        while i < len(salesreps):
            allocations = random.choices(instagram_accounts, k=ration)

            if no_consecutives(allocations) and no_more_than_x(allocations):
                for j in range(ration):
                    if j > len(instagram_accounts):
                        break
                    account = get_object_or_404(Account, id=allocations[j])

                    salesreps[i].instagram.add(account)

                    account.save()
                    print(account.igname)
                    if account.igname:
                        if serializer.data.get("reaction") == 1:
                            cl = login_user(salesreps[i].ig_username, salesreps[i].ig_password)
                            user_id = cl.user_id_from_username(account.igname)
                            user_medias = cl.user_medias(user_id)

                            try:
                                media_id = cl.media_id(media_pk=user_medias[0].pk)
                                random_compliment = get_random_compliment(
                                    salesrep=salesreps[i], compliment_type="first_compliment"
                                )
                                comment = cl.media_comment(media_id, random_compliment)
                            except Exception as error:
                                print(error)

                            ready_accounts = {
                                "comment": comment.dict(),
                                "account": account.igname,
                                "salesrep": salesreps[i].ig_username,
                            }
                            accounts_complimented.append(ready_accounts)
                        elif serializer.data.get("reaction") == 2:
                            try:
                                send_first_compliment.delay(username=account.igname)
                                sent_compliment_status = StatusCheck.objects.get(name="sent_compliment")
                                account.status = sent_compliment_status
                                account.save()

                                try:
                                    schedule, _ = CrontabSchedule.objects.get_or_create(
                                        minute="*/1",
                                        hour="*",
                                        day_of_week="*",
                                        day_of_month="*",
                                        month_of_year="*",
                                    )
                                except Exception as error:
                                    print(error)

                                try:
                                    PeriodicTask.objects.get_or_create(
                                        name="GenerateResponse",
                                        crontab=schedule,
                                        task="instagram.tasks.generate_and_send_response",
                                        start_time=timezone.now(),
                                    )
                                except Exception as error:
                                    print(error)

                                try:
                                    schedule, _ = CrontabSchedule.objects.get_or_create(
                                        minute="*/1",
                                        hour="*",
                                        day_of_week="*",
                                        day_of_month="*",
                                        month_of_year="*",
                                    )
                                except Exception as error:
                                    print(error)

                                try:
                                    PeriodicTask.objects.get_or_create(
                                        name="CheckResponse",
                                        crontab=schedule,
                                        task="instagram.tasks.check_response",
                                        start_time=timezone.now(),
                                    )
                                except Exception as error:
                                    print(error)

                            except Exception as error:
                                print(error)

                            ready_accounts = {
                                "account": account.igname,
                                "salesrep": salesreps[i].ig_username,
                            }
                            accounts_complimented.append(ready_accounts)

                        elif serializer.data.get("reaction") == 3:

                            try:
                                media_id = cl.media_id(media_pk=user_medias[0].pk)
                                cl.media_like(media_id)
                            except Exception as error:
                                print(error)

                            ready_accounts = {
                                "like": True,
                                "account": account.igname,
                                "salesrep": salesreps[i].ig_username,
                                "success": True,
                            }
                            accounts_complimented.append(ready_accounts)

                i += 1

        return Response({"accounts": accounts_complimented})
