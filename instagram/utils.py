from instagram.models import Account, Message, OutSourced, StatusCheck, Thread
from django_celery_beat.models import PeriodicTask, CrontabSchedule
from rest_framework.response import Response
from outreaches.serializers import PeriodicTaskGetSerializer
from outreaches.serializers import PeriodicTaskPostSerializer
from rest_framework import status

def get_account(username):
    account = None
    try:
        first_account = Account.objects.filter(igname="".join(username)).first()
        last_account = Account.objects.filter(igname="".join(username)).last()
        if first_account.salesrep_set.filter().exists():
            account = first_account
        elif last_account.salesrep_set.filter().exists():
            account = last_account
    except Exception as error:
        print(error)
    return account

def get_sales_rep_for_account(username):
    salesrep = None
    account = get_account(username)
    if account:
        salesrep = account.salesrep_set.first()
    return salesrep

def lead_is_for_salesrep(username, salesrep_to_check):
    ret = False
    account_salesrep = get_sales_rep_for_account(username)
    account_sales_rep_igname = account_salesrep.ig_username
    if account_sales_rep_igname == salesrep_to_check:
        ret = True 
    return ret


def tasks_by_sales_rep(task_name, sales_rep, task_status="any", order=1, number=-1):
    tasks = PeriodicTask.objects.filter(task=task_name).order_by('start_time')

    if task_status == "enabled":
        tasks = tasks.filter(enabled=True)
    elif task_status == "disabled":
        tasks = tasks.filter(enabled=False)
    
    if order == -1:
        tasks = tasks.reverse()

    populated_tasks = []
    count = 0

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
            count += 1
            if number != -1 and count == number:
                break
    return Response({'tasks': populated_tasks}, status=status.HTTP_200_OK)