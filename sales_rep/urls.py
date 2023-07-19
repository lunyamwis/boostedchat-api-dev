from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter

from .views import SalesRepListView, SalesRepManager

router = DefaultRouter()
router.register(r"rep", SalesRepManager, basename="rep")


urlpatterns = [
    path('all/', SalesRepListView.as_view(), name='sales_rep'),
    path("", include(router.urls))
]
