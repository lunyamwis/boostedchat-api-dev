from rest_framework import status, viewsets
from rest_framework.response import Response

from .models import Lead
from .serializers import LeadSerializer

# Create your views here.


class LeadManager(viewsets.ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer

    def list(self, request):

        leads = Lead.objects.all()

        response = {"status_code": status.HTTP_200_OK, "instagram": [lead.instagram.values() for lead in leads]}
        return Response(response, status=status.HTTP_200_OK)
