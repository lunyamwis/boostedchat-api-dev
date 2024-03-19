from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from outreaches.views import PeriodicTaskViewSet
# from .views import ReschedulePeriodicTasksAPIView
from . import views


router = routers.DefaultRouter()
router.register(r'periodic-tasks', PeriodicTaskViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('periodic-tasks/types/', PeriodicTaskViewSet.as_view({'get': 'task_types'}), name='task_types'),
    # path('periodic-tasks/reschedule/', ReschedulePeriodicTasksAPIView.as_view(), name='reschedule_tasks'),
    # path('create_vm_and_run_docker/', views.CreateVMAndRunDockerAPIView.as_view(), name='create_vm_and_run_docker'),
    path('', include(router.urls)),
    # path('periodic-tasks/', ReschedulePeriodicTasksAPIView.as_view(), name='list_tasks'),

    # URL pattern for POST requests to reschedule tasks
    # path('periodic-tasks/reschedule/', ReschedulePeriodicTasksAPIView.as_view(), name='reschedule_tasks'),

]