from rest_framework import viewsets
from .models import ExceptionModel

# Create your views here.
class ExceptionViewset(viewsets.ModelViewSet):
    queryset = ExceptionModel.objects.all()

    