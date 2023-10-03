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
from instagram.tasks import send_message

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
                            first_compliment_prompt = f"""
                                Act as if you were an Instagram DM-based sales representative for the biggest beauty appointment management system & marketplace called Booksy. Recommend the personalized compliment to the US-based [get category from the data within the triple backticks] at the beginning of our Instagram DM-based conversation that will help establish the relationship and win the right to ask questions about their problems.
                                Each message needs to be a short DM message in a way that sounds natural and engaging, confirming that we believe that the[get category from the data within the triple backticks] is a great professional and we understand their point of view. make sure to use a tone of voice in line with those characteristics: "We’re revolutionizing the way people make appointments. [get category from the data within the triple backticks] are frustrated from wasting too much time managing their books when they could be focusing on their craft. Booksy offers a platform for them to streamline business management. Both a reliable receptionist and a trustworthy business partner, Booksy helps merchants grow and gives them time to master their skills. CONVERSATIONAL We are a business partner and friendly neighbor recommending a service or business. Our voice needs to match our attitude. Being corporate is too rigid, and can be alienating. Speaking casually and candidly allows customers to trust us. ENCOURAGING Our customers and merchants dream of fulfilling their full personal potential, and Booksy gives them the tools to accomplish that. GENUINE Booksy makes a promise to its customers. We’re adding a new meaning to their lives by redefining what it means to manage a business. How? By being accurate, honest, transparent, and receptive to customer feedback."
                                Possibly relevant information about the person you talk to & their business that you can use: ```
                                {[o_data.results['reviews'] for o_data in account.outsourced_set.all()]}
                                ``` Also don't present booksy at this stage at all, it is only about praising them. Don't let them know that we are booking
                                service provider, check out this examples to help you better frame the compliment:
                                example: Hey [get name from the data within the triple backticks],
                                🌟 I just checked out your profile on [get name from the data within the triple backticks], and I'm seriously impressed with the amazing
                                services you offer at [get business name from the data within the triple backticks]. Your  [Include some of the adjectives or their synonyms
                                [get adjectives from the aboutClientAdjectives within the data in the triple backticks above ] and use them in the conversation.
                                Those are opinions from their clients and they are what distinguish the best professionals. Conclude by wishing them best of luck.
                                Remember the tone of voice above that we mentioned. Don't repeat yourself when using adjectives.] really shine through. 💈✂️.Do not sign off.
                            """
                            try:
                                random_compliment_state = query_gpt(first_compliment_prompt)
                                random_compliment = (
                                    random_compliment_state.get("choices")[0].get("message").get("content")
                                )
                                send_message.delay(random_compliment, username=account.igname)
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
