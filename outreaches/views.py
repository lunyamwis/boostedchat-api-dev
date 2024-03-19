from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.http import require_GET
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json
from django.shortcuts import render
from rest_framework import viewsets
from .serializers import PeriodicTaskGetSerializer
from .serializers import PeriodicTaskPostSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.utils import timezone
from celery import current_app
import logging


# class PeriodicTaskViewSet(viewsets.ModelViewSet):
#     queryset = PeriodicTask.objects.all()
#     serializer_class = PeriodicTaskSerializer
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

 
    def create(self, request, *args, **kwargs):
        task_name = request.data.get('task', None)  # Get the task name from request data
        if task_name:
            queryset = PeriodicTask.objects.filter(task=task_name)
            serializer = self.get_serializer(queryset, many=True)
            start_date = timezone.now().day  # Use the current date as start_date
            start_month = timezone.now().month  # Use the current month as start_month
            start_hour = request.data.get('startTime', 0)  # Get start_hour from request data
            start_minute = request.data.get('startMinute', 0)  # Get start_minute from request data
            first_day_start_hour = int(start_hour)
            first_day_start_minute = int(start_minute)
            hours_per_day = 12 # int(request.data.get('numperDay', 12))  # Get hours_per_day from request data
            tasks_per_day = int(request.data.get('numperDay', 48))  # Get tasks_per_day from request data

            total_tasks = PeriodicTask.objects.filter(task=task_name).count()
            scheduler_list = generate_scheduler(start_date, start_month, start_hour, start_minute,
                                                first_day_start_hour, first_day_start_minute,
                                                hours_per_day, tasks_per_day, total_tasks)

            # Set the scheduler for each task and save
            for index, scheduler in enumerate(scheduler_list):
                # Split the scheduler string into components
                print(scheduler)
                minute, hour, day, month, _, _, _ = scheduler.split()

                # Convert the components to integers
                minute = int(minute)
                hour = int(hour)
                day = int(day)
                month = int(month)
                print(111111)
                # Create a datetime object for the scheduler
                scheduler_datetime = timezone.datetime(year=timezone.now().year, month=month, day=day, hour=hour, minute=minute)
                # print(scheduler_datetime)
                print(2222222)
                task = queryset.order_by('-id')[index]
                print(33333)
                task.start_time = scheduler_datetime
                # task.save()
                task.enabled = True
                print(444444)
                # Create a CrontabSchedule object for the task
                crontab_schedule = CrontabSchedule.objects.create(
                    minute=scheduler_datetime.minute,
                    hour=scheduler_datetime.hour,
                    day_of_month=scheduler_datetime.day,
                    month_of_year=scheduler_datetime.month,
                    timezone='UTC'  # Set the timezone explicitly
                )
                task.crontab = crontab_schedule
                print(5555555555)
                task.save()

                # Remove the old task from Celery if it exists
                # try:
                #     current_app.conf.beat_schedule.pop(task.name)
                # except KeyError:
                #     print("passing...")
                #     pass  # Task not found in Celery schedule
                # print(task.name)
                # schedule = CrontabSchedule.objects.create(
                #     minute=serializer.data.get('minute'),
                #     hour=serializer.data.get('hour'),
                #     day_of_week="*",
                #     day_of_month=serializer.data.get('day_of_month'),
                #     month_of_year=serializer.data.get('month_of_year'),
                # )
                print("starting to save")
                try:
                    PeriodicTask.objects.update_or_create(
                        name=task.name,
                        crontab=task.crontab,
                        task=task_name,
                        args=task.args
                    )
                
                except Exception as error:
                    logging.warning(error)
                print(task)
            print("done rescheduling")
            queryset = self.queryset.filter(task=task_name)
            queryset = self.queryset.all()
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
            # return Response({'task': 'Task name not provided'})
        else:
            return Response({'error': 'Task name not provided'}, status=status.HTTP_400_BAD_REQUEST)

    
    @action(detail=False, methods=['get'])
    def task_types(self, request, *args, **kwargs):
        task_types = self.queryset.values_list('task', flat=True).distinct()
        return Response(task_types)
    

def generate_scheduler(start_date, start_month, start_hour, start_minute, first_day_start_hour, first_day_start_minute, hours_per_day, tasks_per_day, total_tasks):
    # Convert necessary parameters to integers
    start_date = int(start_date)
    start_month = int(start_month)
    start_hour = int(start_hour)
    start_minute = int(start_minute)
    first_day_start_hour = int(first_day_start_hour)
    first_day_start_minute = int(first_day_start_minute)
    hours_per_day = int(hours_per_day)
    tasks_per_day = int(tasks_per_day)

    # Initialize variables
    task_minute = first_day_start_minute
    task_date = start_date
    task_hour = first_day_start_hour
    minutes_per_task = (hours_per_day * 60) // tasks_per_day  # Use integer division here
    task_month = start_month
    scheduler_list = []

    # Generate scheduler for each task
    for _ in range(total_tasks):
        utc_minute = task_minute
        utc_hour = task_hour
        utc_date = task_date
        utc_month = task_month

        # Ensure utc_minute is within valid range
        if utc_minute < 0:
            utc_minute = 0
        elif utc_minute > 59:
            utc_minute = 59

        # Handle hour overflow
        if utc_hour >= 24:
            utc_date += 1
            utc_hour -= 24

        # Handle date overflow
        if utc_hour < 0:
            utc_date -= 1
            utc_hour = 24 + utc_hour

        # Handle month boundaries
        if utc_date > days_in_month(utc_month):
            utc_date = 1
            utc_month += 1

        # Handle year boundary
        if utc_month > 12:
            utc_month = 1

        scheduler_list.append(f'{utc_minute} {utc_hour} {utc_date} {utc_month} * (m/h/dM/MY/d) UTC')

        # Update task time for the next task
        task_minute += minutes_per_task

        if task_minute >= 60:
            task_hour += 1
            task_minute -= 60

        if task_hour > start_hour + hours_per_day - 1:
            if task_hour - (start_hour + hours_per_day - 1) == 1 and task_minute == 0:
                task_minute = 59
                task_hour = start_hour + hours_per_day - 1
            else:
                task_date += 1
                task_minute = start_minute
                task_hour = start_hour

    return scheduler_list

def days_in_month(month):
    # Define days in each month (assuming non-leap year for simplicity)
    days_in_month = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    return days_in_month[month]

# class ReschedulePeriodicTasksAPIView(APIView):
#     permission_classes = [AllowAny]

#     @require_POST
#     def post(self, request, *args, **kwargs):
#         # task_type = request.data.get('task_type', None)
#         # if task_type:
#         #     queryset = PeriodicTask.objects.filter(task=task_type)
#         # else:
#         #     queryset = PeriodicTask.objects.all()
#         # serializer = PeriodicTaskPostSerializer(queryset, many=True)
#         # return Response(serializer.data)
#         serializer = PeriodicTaskPostSerializer(data=request.data)  # Data now expects just 'task'
#         if serializer.is_valid():
#             # serializer.save()
#             return Response(serializer.data, status=201)
#         return Response(serializer.errors, status=400)
#     # def get(self, request, *args, **kwargs):
#     #     try:
#     #         # Fetch all tasks from the PeriodicTask model
#     #         tasks = PeriodicTask.objects.all()

#     #         # List all tasks (you can modify this output format as needed)
#     #         task_list = [{'id': task.id, 'name': task.name} for task in tasks]

#     #         return JsonResponse({'success': True, 'tasks': task_list})
#     #     except Exception as e:
#     #         return JsonResponse({'success': False, 'error_message': str(e)})