from rest_framework import viewsets

from .models import SalesRep
from .serializers import SalesRepSerializer

# Create your views here.


class SalesRepManager(viewsets.ModelViewSet):
    queryset = SalesRep.objects.all()
    serializer_class = SalesRepSerializer
