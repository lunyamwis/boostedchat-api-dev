from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import SalesRepManager

router = DefaultRouter()
router.register(r"rep", SalesRepManager, basename="rep")


urlpatterns = [path("", include(router.urls))]
