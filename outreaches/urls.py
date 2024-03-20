from django.urls import path, include
from rest_framework import routers
from outreaches.views import PeriodicTaskViewSet


router = routers.DefaultRouter()
router.register(r'periodic-tasks', PeriodicTaskViewSet)

urlpatterns = [
    path('periodic-tasks/types/', PeriodicTaskViewSet.as_view({'get': 'task_types'}), name='task_types'),
    path('', include(router.urls)),

]