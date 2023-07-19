import math
import random

from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.models import User
from instagram.models import Account

from .helpers.task_allocation import no_consecutives, no_more_than_x
from .models import SalesRep
from .serializers import SalesRepListSerializer, SalesRepSerializer

# Create your views here.


class SalesRepManager(viewsets.ModelViewSet):
    queryset = SalesRep.objects.all()
    serializer_class = SalesRepSerializer

    def list(self, request):

        reps = SalesRep.objects.all()
        user_info = []
        for rep in reps:
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
        ready_accounts = {}

        while i < len(salesreps):
            allocations = random.choices(instagram_accounts, k=ration)

            if no_consecutives(allocations) and no_more_than_x(allocations):
                for j in range(ration):
                    if j > len(instagram_accounts):
                        break
                    salesreps[i].instagram.add(get_object_or_404(Account, id=allocations[j]))
                i += 1

        return Response({"accounts": ready_accounts})


class SalesRepListView(APIView):
    serializer_class = SalesRepListSerializer
    permission_classes = (AllowAny,)

    def get(self, request):

        users = SalesRep.objects.all()
        serializer = self.serializer_class(users, many=True)
        response = {"status_code": status.HTTP_200_OK, "sales_reps": serializer.data}
        return Response(response, status=status.HTTP_200_OK)
