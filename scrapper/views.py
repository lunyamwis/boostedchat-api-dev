from rest_framework.views import APIView

from .serializers import GmapSerializer

# Create your views here.


class GmapScrapper(APIView):
    serializer_class = GmapSerializer
