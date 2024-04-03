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
# from django.db.models import QuerySet
from instagram.models import Thread, Account
import random
from datetime import time
import time as timer



# # class PeriodicTaskViewSet(viewsets.ModelViewSet):
# #     queryset = PeriodicTask.objects.all()
# #     serializer_class = PeriodicTaskSerializer
# class RescheduleTaskViewSet(viewsets.ModelViewSet):
#     # queryset = PeriodicTask.objects.all()
#     def get_queryset(self):
#         return None #QuerySet.none(self)  # Ret


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
    
from datetime import datetime, timedelta

def time_parts(time):
    return time.year, time.month, time.day, time.hour, time.minute

def add_minutes_to_time(input_time, minutes): # interval is in minutes
    if isinstance(input_time, datetime):
        try:
            # Create a timedelta object with the specified number of minutes
            time_delta = timedelta(minutes=minutes)
            # Add the timedelta to the input time
            new_time = input_time + time_delta
            return new_time  # Return the new time as a datetime object
        except ValueError:
            print("wrong minutes")
            return None  # Handle invalid time format
    else:
        print("is not date time")
        return None  # Handle non-datetime input

def get_task_interval_minutes(hours_per_day, tasks_per_day):
    if tasks_per_day < 0 or hours_per_day < 0:
        raise ValueError("Hours per day and tasks per day must be non-negative.")
    if tasks_per_day == 0 or hours_per_day == 0:
        return 0
    return (hours_per_day * 60) // tasks_per_day  # use integer division

def randomize_interval(interval_minutes, seed_minutes, direction):
    if interval_minutes < 0 or seed_minutes < 0:
        raise ValueError("interval_minutes and seed_minutes must be non-negative")
    interval_head = int(0.25 * interval_minutes)  # Convert interval_head to an integer

    if direction == 0:
        # Random integer between -interval_head and +interval_head
        random_value = random.randint(-interval_head, interval_head)
    elif direction == -1:
        # Random integer between -interval_head and 0
        random_value = random.randint(-interval_head, 0)
    elif direction == 1:
        # Random integer between 0 and +interval_head
        random_value = random.randint(0, interval_head)
    else:
        raise ValueError("Invalid direction. Direction should be -1, 0, or 1.")

    return random_value + seed_minutes  # Add the random value to the seed_minutes

def get_first_time(start_time, interval_minutes):
    interval_minutes = randomize_interval(interval_minutes, 0, 1)
    print(f'=>{start_time}')
    print(f'=========>{interval_minutes}')
    return add_minutes_to_time(start_time, interval_minutes)

def get_next_time(current_time, interval_minutes):
    interval_minutes = randomize_interval(interval_minutes, interval_minutes, 0)
    return add_minutes_to_time(current_time, interval_minutes)

def not_in_interval(current_task_time, daily_start_time, daily_end_time):
    start_hour = daily_start_time
    stop_hour = daily_end_time
    current_hour = current_task_time.hour  # Get the hour from current_task_time
    
    if stop_hour == start_hour:
        return False  # always in work interval
    if stop_hour < start_hour:
        if current_hour >= start_hour or current_hour < stop_hour:
            return False  # in work interval
        return True 
    if current_hour >= start_hour and current_hour < stop_hour:
        return False  # in work interval
    return True

# run = 0
def put_within_working_hour(current_task_time, start_hour, stop_hour ):
    # global run 
    stop_hour_init = stop_hour
    if not_in_interval(current_task_time, start_hour, stop_hour):
        working_interval = stop_hour - start_hour
        if stop_hour < start_hour:
            working_interval += 24
        not_working_interval = 24 - working_interval
        current_task_time = add_minutes_to_time(current_task_time, not_working_interval * 60)
        if not_in_interval(current_task_time, start_hour, stop_hour):
            # print(f'300==> {current_task_time}...{start_hour}, {stop_hour}')
            # run += 1
            # if run == 10:
            #     raise Exception(f"func error ")
            current_task_time = put_within_working_hour(current_task_time, start_hour, stop_hour_init )
        else:
            run = 0
    return current_task_time

def chron_parts(chron):
    current_year = datetime.now().year
    return current_year, chron.month_of_year, chron.day_of_month, chron.hour, chron.minute
    
def scheduler_tasks(tasks, start_time, hours_per_day, tasks_per_day, daily_start_time, daily_end_time): 
    interval_minutes = get_task_interval_minutes(hours_per_day, tasks_per_day)
    print(start_time, interval_minutes)
    current_task_time = get_first_time(start_time, interval_minutes)
    print(current_task_time, interval_minutes)
    current_task_time = put_within_working_hour(current_task_time, daily_start_time, daily_end_time )
    print(current_task_time)

    for task in tasks:
        year, month, day, hour, minute = time_parts(current_task_time)
        scheduler_datetime = timezone.datetime(year=year, month=month, day=day, hour=hour, minute=minute)
        crontab_schedule = CrontabSchedule.objects.create(
                    minute=scheduler_datetime.minute,
                    hour=scheduler_datetime.hour,
                    day_of_month=scheduler_datetime.day,
                    month_of_year=scheduler_datetime.month,
                    timezone='UTC'  # Set the timezone explicitly
                )
        task.enabled = True
        task.start_time = scheduler_datetime  
        task.crontab = crontab_schedule
        # task.save()
        # try:
        #     PeriodicTask.objects.update_or_create(
        #         name=task.name,
        #         crontab=task.crontab,
        #         task=task_name,
        #         args=task.args
        #     )
        
        # except Exception as error:
        #     logging.warning(error)

        current_task_time = get_next_time(current_task_time, interval_minutes)
        current_task_time = put_within_working_hour(current_task_time, daily_start_time, daily_end_time )

    return tasks # save where this is called from

def process_task(task_name, username, enable=True):
        queryset = PeriodicTask.objects.filter(task=task_name, name=username)

        if queryset.exists():
            for task in queryset:
                if task.enabled == enable:  # Check if already in the desired state
                    return Response({'error': f'Task is already {"enabled" if enable else "disabled"}'}, 
                                    status=status.HTTP_422_UNPROCESSABLE_ENTITY)

                task.enabled = enable
                task.save()
                return Response({'message': f'Task {"enabled" if enable else "disabled"}'})
        else:
            return Response({'error': f'Task: {task_name} not found for {username}'}, 
                            status=status.HTTP_404_NOT_FOUND)

def process_reschedule_single_task(task_name, username, start_hour, start_minute, tasks_per_day=48):
    queryset = PeriodicTask.objects.filter(task=task_name, name=username).order_by('-id')
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
    start_hour = int(start_hour)  # Convert start_hour to integer if it's not already
    start_minute = int(start_minute)  # Convert start_minute to integer if it's not already

    # start_time = time(hour=start_hour, minute=start_minute)
    start_time = datetime.now().replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)

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
    queryset = PeriodicTask.objects.filter(task=task_name, name=username).order_by('id')
    serializer = PeriodicTaskGetSerializer(queryset, many=True)
    return Response(serializer.data)

def ig_thread_exists(username):
    try:
        first_account = Account.objects.filter(igname="".join(username)).first()
        last_account = Account.objects.filter(igname="".join(username)).last()
        if first_account.salesrep_set.filter().exists():
            account = first_account
        elif last_account.salesrep_set.filter().exists():
            account = last_account
    except Exception as error:
        print(error)
        return True # assume true
    salesrep = account.salesrep_set.first()
    ig_username = salesrep.ig_username
    print(f'Checking....{username}=>{ig_username}')
    if  Thread.objects.filter(account__igname=username, account__salesrep__ig_username=ig_username): # try this one tomorrow
    # if  Thread.objects.filter(account__igname=username):
        print(f"exist for /|\\")
        return True
    else:
        return False