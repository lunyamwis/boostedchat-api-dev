from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_GET
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json
from django.shortcuts import render
from rest_framework import viewsets
from .serializers import PeriodicTaskGetSerializer
from .serializers import PeriodicTaskPostSerializer, TaskBySalesRepSerializer, FirstComplimentViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status

from celery import current_app
import logging
# from django.db.models import QuerySet
import random
from datetime import time
import time as timer

from instagram.utils import lead_is_for_salesrep, tasks_by_sales_rep
# from instagram.tasks import send_first_compliment
from .utils import *

# # class PeriodicTaskViewSet(viewsets.ModelViewSet):
# #     queryset = PeriodicTask.objects.all()
# #     serializer_class = PeriodicTaskSerializer
# class RescheduleTaskViewSet(viewsets.ModelViewSet):
#     # queryset = PeriodicTask.objects.all()
#     def get_queryset(self):
#         return None #QuerySet.none(self)  # Ret


class FirstComplimentViewSet(viewsets.ModelViewSet):
    queryset = PeriodicTask.objects.all()
    def get_serializer_class(self):
        return FirstComplimentViewSet
    
    @action(detail=False, methods=['post'])
    def send_first_compliment(self, request):
        serializer = TaskBySalesRepSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        task_name = validated_data.get('task', None)
        user = validated_data.get('user', None)
        # send_first_compliment(user)

        return Response({'message': f'Sent first compliment for: {user}'})
    
class AbusoViewSet(viewsets.ModelViewSet):
    queryset = PeriodicTask.objects.all()
    # serializer_class = PeriodicTaskGetSerializer
    def get_serializer_class(self):
        return TaskBySalesRepSerializer
    
    @action(detail=False, methods=['post'])
    def tasks_by_sales_rep(self, request, task_name=None, sales_rep=None):
        serializer = TaskBySalesRepSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        task_name = validated_data.get('task', None)
        sales_rep = validated_data.get('sales_rep', None)
        status = validated_data.get('status', "any")
        order = validated_data.get('order', 1)
        number = validated_data.get('number', -1)
        return tasks_by_sales_rep(task_name, sales_rep, status, order, number)
    
class PeriodicTaskViewSet(viewsets.ModelViewSet):
    queryset = PeriodicTask.objects.all()
    # serializer_class = PeriodicTaskGetSerializer

    def list(self, request, *args, **kwargs):
        task_type = request.query_params.get('task', None)
        if task_type:
            queryset = self.queryset.filter(task=task_type)
        else:
            queryset = self.queryset.all()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def get_serializer_class(self):
        if self.action == 'list':  # Use different serializer for list action
            return PeriodicTaskGetSerializer
        else:  # Use default serializer class for other actions
            return PeriodicTaskPostSerializer

    @action(detail=False, methods=['get']) # this performs nothing at all
    def reschedule_last_enabled(self, request, *args, **kwargs):

        task = PeriodicTask.objects.filter(task="instagram.tasks.send_first_compliment", enabled=True).order_by('start_time').last()
        if task:
            print(task.name)
        return Response({'error': 'Task name not provided'}, status=status.HTTP_400_BAD_REQUEST)

 
    def create(self, request, *args, **kwargs):
        task_name = request.data.get('task', None)  # Get the task name from request data
        if task_name:
            queryset = PeriodicTask.objects.filter(task=task_name).order_by('-id')
            filtered_queryset = [] 
            if queryset.exists():
                for task in queryset:
                    args_json = task.args
                    args_list = json.loads(args_json)
                    if args_list and len(args_list) > 0:
                        usernameInner = args_list[0]
                        if isinstance(usernameInner, list):
                            usernameInner = usernameInner[0]
                        thread_exists = ig_thread_exists(usernameInner)
                        if not thread_exists:  # Get salesrep_username from task 
                            filtered_queryset.append(task)
                        else:
                            print(f'Thread exist for {usernameInner}')
            queryset = filtered_queryset
            queryset = PeriodicTask.objects.filter(id__in=[task.id for task in filtered_queryset])

            # serializer = self.get_serializer(queryset, many=True)
            start_hour = request.data.get('startTime', '0')  # Get start_hour from request data # supplied time is in UTC
            start_minute = request.data.get('startMinute', '0')  # Get start_minute from request data
            start_hour = int(start_hour)  # Convert start_hour to integer if it's not already
            start_minute = int(start_minute)  # Convert start_minute to integer if it's not already

            # start_time = time(hour=start_hour, minute=start_minute)
            start_time = datetime.now().replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)

            tasks_per_day = int(request.data.get('numperDay', 48))  # Get tasks_per_day from request data

            # for now we can make do with the hardcoded interval
            hours_per_day = 12 # int(request.data.get('numperDay', 12))  # Get hours_per_day from request data
            daily_start_time = 14
            daily_end_time = daily_start_time + hours_per_day
            if daily_end_time >=24 :
                daily_end_time -= 24

            tasks = scheduler_tasks(queryset, start_time, hours_per_day, tasks_per_day, daily_start_time, daily_end_time)
            for task in tasks:
                task.save()  # Save the task object to the database
                try:
                    PeriodicTask.objects.update_or_create(
                    # PeriodicTask.objects.create(
                        enabled=True,
                        name=task.name,
                        crontab=task.crontab,
                        task=task_name,  # Assuming you have a 'task_name' variable 
                        args=task.args      # Assuming your task has arguments
                    )
                except Exception as error:
                    logging.warning(error)  # Log any errors that might occur
            queryset = PeriodicTask.objects.filter(task=task_name).order_by('id')
            serializer = PeriodicTaskGetSerializer(queryset, many=True)
            return Response(serializer.data)
            # return Response({'task': 'Task name not provided'})
        else:
            return Response({'error': 'Task name not provided'}, status=status.HTTP_400_BAD_REQUEST)

    
    @action(detail=False, methods=['get'])
    def task_types(self, request, *args, **kwargs):
        task_types = self.queryset.values_list('task', flat=True).distinct()
        return Response(task_types)

    @action(detail=False, methods=['post'])
    def reschedule_by_taskname(self, request):
        task_name = request.data.get('task_name')
        tasks = self.queryset.filter(task_name=task_name)
        # Logic to reschedule tasks by task name
        for task in tasks:
            # Your rescheduling logic here
            pass  # Placeholder for actual logic
        return Response({'message': f'Rescheduled tasks with task name: {task_name}'})

    @action(detail=False, methods=['post'])
    def reschedule_by_salesrep(self, request):
        sales_rep = request.data.get('sales_rep')
        tasks = self.queryset.filter(sales_rep=sales_rep)
        # Logic to reschedule tasks by sales rep
        for task in tasks:
            # Your rescheduling logic here
            pass  # Placeholder for actual logic
        return Response({'message': f'Rescheduled tasks with sales rep: {sales_rep}'})

    @action(detail=False, methods=['post'])
    def reschedule_single_task_by_username(self, request):
        username = request.data.get('username')
        task = self.queryset.get(username=username)
        # Logic to reschedule the single task by username
        # Your rescheduling logic here
        return Response({'message': f'Rescheduled single task for username: {username}'})

# instagram.tasks.send_first_compliment
    @action(detail=False, methods=['post'])
    def enable_all_tasks(self, request):
        task_name = request.data.get('task', None)  # Get the task name from request data
        if task_name:
            self.enableOrDisableAll(task_name, True)
            return Response({'message': f'Enabled all {task_name} tasks'})
        else:
            return Response({'error': 'Task name not provided'}, status=status.HTTP_400_BAD_REQUEST)

    def enableOrDisableAll(self, task_name, status):
        queryset = PeriodicTask.objects.filter(task=task_name)
        tasks = queryset.all()
        for task in tasks:
            if task.enabled != status:
                task.enabled = status 
                task.save()


    @action(detail=False, methods=['post'])
    def disable_all_tasks(self, request):
        task_name = request.data.get('task', None)  # Get the task name from request data
        if task_name:
            self.enableOrDisableAll(task_name, False)
            # queryset = PeriodicTask.objects.filter(task=task_name)
            # tasks = self.queryset.all()
            # # Logic to disable all tasks
            # for task in tasks:
            #     task.enabled = False  # Example logic to disable tasks
            #     task.save()
            return Response({'message': 'Disabled all tasks'})
        else:
            return Response({'error': 'Task name not provided'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def disable_all_IG_first_compliment(self, request):
        task_name = "instagram.tasks.send_first_compliment"
        self.enableOrDisableAll(task_name, False)
        return Response({'message': 'Disabled all tasks'})

    @action(detail=False, methods=['get'])
    def enable_all_IG_first_compliment(self, request):
        task_name = "instagram.tasks.send_first_compliment"
        self.enableOrDisableAll(task_name, True)
        return Response({'message': 'Disabled all tasks'})
    
    
    # @action(detail=False, methods=['get'], url_path='by-sales-rep/(?P<task_name>[^/.]+)/(?P<sales_rep>[^/.]+)')
    # def tasks_by_sales_rep(self, request, task_name=None, sales_rep=None):
        
    # @action(detail=False, methods=['post'])
    # def tasks_by_sales_rep(self, request, task_name=None, sales_rep=None):
    #     serializer = TaskBySalesRepSerializer(data=request.data)
    #     serializer.is_valid(raise_exception=True)
    #     validated_data = serializer.validated_data

    #     task_name = validated_data.get('task', None)
    #     sales_rep = validated_data.get('sales_rep', None)
    #     status = validated_data.get('status', "any")
    #     order = validated_data.get('order', 1)
    #     number = validated_data.get('number', -1)
    #     return tasks_by_sales_rep(task_name, sales_rep, status, order, number)

    @action(detail=False, methods=['post'])
    def reschedule_last_disabled_task(self, request):
        last_disabled_task = self.queryset.filter(enabled=False).order_by('-id').first()
        # Logic to reschedule the last disabled task
        if last_disabled_task:
            # Your rescheduling logic here
            pass  # Placeholder for actual logic
        return Response({'message': 'Rescheduled last disabled task'}) 

    @action(detail=False, methods=['post'])
    def enable_single_task(self, request):
        task_name = request.data.get('task', None)
        username = request.data.get('user', None) 

        if task_name and username:
            return process_task(task_name, username, True)  # Call the helper function
        else:
            return Response({'error': 'Task name and username are required'}, 
                            status=status.HTTP_400_BAD_REQUEST)
                            
    @action(detail=False, methods=['post'])
    def disable_single_task(self, request):
        task_name = request.data.get('task', None)
        username = request.data.get('user', None) 

        if task_name and username:
            return process_task(task_name, username, False)  # Call the helper function
        else:
            return Response({'error': 'Task name and username are required'}, 
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def reschedule_single_task(self, request):
        task_name = request.data.get('task', None)  # Get the task name from request data
        username = request.data.get('user', None) 
        start_hour = request.data.get('startTime', '0')  # Get start_hour from request data # supplied time is in UTC
        start_minute = request.data.get('startMinute', '0')  # Get start_minute from request data
        tasks_per_day = int(request.data.get('numperDay', 48))  # Get tasks_per_day from request data
        if task_name  and username:
           return process_reschedule_single_task(task_name, username, start_hour, start_minute, tasks_per_day)
        else:
            return Response({'error': 'Task name and username are required'}, 
                            status=status.HTTP_400_BAD_REQUEST)
    
