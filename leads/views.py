from rest_framework import status, viewsets
from rest_framework.response import Response

from instagram.models import Account

from .models import Lead
from .serializers import LeadSerializer

# Create your views here.


class LeadManager(viewsets.ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer

    def list(self, request):

        leads = Lead.objects.all()
        instagram_accounts = []
        for lead in leads:
            instagram_accounts.append(Account.objects.filter(id=lead.instagram.id).values())

        response = {"status_code": status.HTTP_200_OK, "instagram": instagram_accounts}
        return Response(response, status=status.HTTP_200_OK)
