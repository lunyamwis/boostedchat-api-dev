from django.urls import path, include
from rest_framework import routers
from outreaches.views import PeriodicTaskViewSet, AbusoViewSet, FirstComplimentViewSet


router = routers.DefaultRouter()
router.register(r'periodic-tasks', PeriodicTaskViewSet)

urlpatterns = [
    # path('periodic-tasks/by-sales-rep/<str:task_name>/<str:sales_rep>/', PeriodicTaskViewSet.as_view({'get': 'tasks_by_sales_rep'}), name='tasks_by_sales_rep'),
    path('periodic-tasks/send_first_compliment/', FirstComplimentViewSet.as_view({'post': 'send_first_compliment'}), name='send_first_compliment'),
    path('periodic-tasks/tasks_by_sales_rep/', AbusoViewSet.as_view({'post': 'tasks_by_sales_rep'}), name='tasks_by_sales_rep'),
    path('periodic-tasks/reschedule/taskname/<str:task_name>/', PeriodicTaskViewSet.as_view({'post': 'reschedule_by_taskname'}), name='reschedule_taskname'),
    # path('periodic-tasks/reschedule/salesrep/<str:sales_rep>/', PeriodicTaskViewSet.as_view({'post': 'reschedule_by_salesrep'}), name='reschedule_salesrep'),
    # path('periodic-tasks/reschedule/username/<str:username>/', PeriodicTaskViewSet.as_view({'post': 'reschedule_single_task_by_username'}), name='reschedule_username'),
    path('periodic-tasks/reschedule_single_task/', PeriodicTaskViewSet.as_view({'post': 'reschedule_single_task'}), name='reschedule_single_task'),
    path('periodic-tasks/enable-single/', PeriodicTaskViewSet.as_view({'post': 'enable_single_task'}), name='enable_single'),
    path('periodic-tasks/disable-single/', PeriodicTaskViewSet.as_view({'post': 'disable_single_task'}), name='disable_single'),
    path('periodic-tasks/enable-all/', PeriodicTaskViewSet.as_view({'post': 'enable_all_tasks'}), name='enable_all'),
    path('periodic-tasks/disable-all/', PeriodicTaskViewSet.as_view({'post': 'disable_all_tasks'}), name='disable_all'),
    path('periodic-tasks/disable-all-ig-first/', PeriodicTaskViewSet.as_view({'post': 'disable_all_IG_first_compliment'}), name='disable_all_IG_firt'),
    path('periodic-tasks/enable-all-ig-first/', PeriodicTaskViewSet.as_view({'post': 'enable_all_IG_first_compliment'}), name='enable_all_IG_first'),
    # path('periodic-tasks/reschedule-last-disabled/', PeriodicTaskViewSet.as_view({'post': 'reschedule_last_disabled_task'}), name='reschedule_last_disabled'),
    path('periodic-tasks/types/', PeriodicTaskViewSet.as_view({'get': 'task_types'}), name='task_types'),
    # path('periodic-tasks/reschedule_last_enabled/', PeriodicTaskViewSet.as_view({'get': 'reschedule_last_enabled'}), name='reschedule_last_enabled'),
    path('', include(router.urls)),  # Include router URLs for the viewset
]