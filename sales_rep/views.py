import math
import random

from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from authentication.models import User
from instagram.helpers.login import login_user
from instagram.models import Account

from .helpers.task_allocation import no_consecutives, no_more_than_x
from .models import SalesRep
from .serializers import SalesRepSerializer

# Create your views here.
COMPLIMENTS = {
    "the_old_school_gentleman": "Loving the classic touch you bring to every cut. It's timeless.",
    "the_fashion_forward_stylist": "Your styles are always runway-ready. Ahead of the curve!",
    "the_family_barber": "You've got a knack for making the whole family look great. A gem in the community!",
    "the_eco_artist": "Your green approach to grooming is not just refreshing but responsible. 🌿",
}


class SalesRepManager(viewsets.ModelViewSet):
    queryset = SalesRep.objects.all()
    serializer_class = SalesRepSerializer

    def list(self, request):

        reps = SalesRep.objects.all()
        user_info = []
        for rep in reps:
            if User.objects.filter(id=rep.user.id).exists():
                info = {"user": User.objects.filter(id=rep.user.id).values(), "instagram": rep.instagram.values()}
                user_info.append(info)

        response = {"status_code": status.HTTP_200_OK, "info": user_info}
        return Response(response, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"], url_path="assign-accounts")
    def assign_accounts(self, request, pk=None):
        instagram_accounts = [i.id for i in Account.objects.all()]
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

                    cl = login_user(salesreps[i].ig_username, salesreps[i].ig_password)
                    if account.igname:
                        user_id = cl.user_id_from_username(account.igname)
                        user_medias = cl.user_medias(user_id)

                        print(user_medias[0])
                        try:
                            media_id = cl.media_id(media_pk=user_medias[0].pk)
                        except Exception as error:
                            print(error)
                        dict_items = list(COMPLIMENTS.items())
                        random_item = random.choice(dict_items)
                        _, random_compliment = random_item
                        comment = cl.media_comment(media_id, random_compliment)
                        ready_accounts = {
                            "comment": comment.dict(),
                            "account": account.igname,
                            "salesrep": salesreps[i].ig_username,
                        }
                        accounts_complimented.append(ready_accounts)

                i += 1

        return Response({"accounts": accounts_complimented})
