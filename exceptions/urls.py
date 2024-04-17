from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'exceptions', views.ExceptionViewset, basename='exceptions')

urlpatterns = [
    path('', include(router.urls)),  # Include router URLs for the viewset
]