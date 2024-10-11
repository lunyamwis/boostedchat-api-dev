import random
from instagram.models import Account, Message, OutSourced, StatusCheck, Thread
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from rest_framework.response import Response
from outreaches.serializers import PeriodicTaskGetSerializer
from outreaches.serializers import PeriodicTaskPostSerializer
from sales_rep.models import SalesRep
from rest_framework import status
from datetime import datetime, timedelta

def assign_salesrep(account):
    salesrep = None
    try:
        available_sales_reps = SalesRep.objects.filter(available=True)
        random_salesrep_index = random.randint(0,len(available_sales_reps)-1)
        available_sales_reps[random_salesrep_index].instagram.add(account)
        salesrep = available_sales_reps[random_salesrep_index]
    except Exception as err:
        print(err)
    return salesrep


def get_account(username):
    account = None
    try:
        first_account = Account.objects.filter(igname__icontains=''.join(username).split('-')[0]).latest('created_at')
        last_account = Account.objects.filter(igname__icontains=''.join(username).split('-')[0]).last()
        if first_account.salesrep_set.exists():
            account = first_account
        elif last_account.salesrep_set.exists():
            account = last_account
        else:
            assign_salesrep(last_account)
            account = last_account

    except Exception as error:
        print(error)
    return account



def get_sales_rep_for_account(username):
    salesrep = None
    username = username
    account = get_account(username)
    if account:
        if account.salesrep_set.exists():
            salesrep = account.salesrep_set.first()
        
    return salesrep

def lead_is_for_salesrep(username, salesrep_to_check):
    ret = False
    account_salesrep = get_sales_rep_for_account(username)
    account_sales_rep_igname = account_salesrep.ig_username

    if account_sales_rep_igname == salesrep_to_check:
        ret = True 
    return ret


def tasks_by_sales_rep(task_name, sales_rep, task_status="any", order=1, number=-1, ret_tasks = False):
    tasks = PeriodicTask.objects.filter(task=task_name).order_by('start_time')

    if task_status == "enabled":
        tasks = tasks.filter(enabled=True)
    elif task_status == "disabled":
        tasks = tasks.filter(enabled=False)
    
    if order == -1:
        tasks = tasks.reverse()

    populated_tasks = []
    count = 0

    task_objs = []

    for task in tasks:
        lead_user_name = task.name.replace("SendFirstCompliment-", "")
        if lead_is_for_salesrep(lead_user_name, sales_rep):
            # any status
            serializer = PeriodicTaskGetSerializer(task)
            serialized_task = serializer.data
            # Populate object to return
            populated_task = {
                'task': serialized_task,
                'sales_rep': sales_rep,
            }
            populated_tasks.append(populated_task)
            task_objs.append(task)
            count += 1
            if number != -1 and count == number:
                break
    if ret_tasks:
        return task_objs
    return Response({'tasks': populated_tasks}, status=status.HTTP_200_OK)




def generate_time_slots(start_datetime, end_datetime, interval):
    start = datetime.strptime(start_datetime, "%Y-%m-%d %H:%M")
    end = datetime.strptime(end_datetime, "%Y-%m-%d %H:%M")
    time_slots = []

    while start <= end:
        time_slots.append(start)
        start += timedelta(minutes=interval)

    return time_slots