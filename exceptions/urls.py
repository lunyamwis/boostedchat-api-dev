from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.DefaultRouter()
router.register(r'exceptions', TasksViewSet, basename='tasks')
router.register(r'task', TaskViewSet, basename='task')
router.register(r'periodic-tasks', PeriodicTaskViewSet)

urlpatterns = [
    path('', include(router.urls)),  # Include router URLs for the viewset
]