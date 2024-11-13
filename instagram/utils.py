import random
import requests
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
        accounts = Account.objects.filter(igname__icontains=''.join(username).split('-')[0]).exclude(status__name='sent_compliment') 
        account = accounts.latest('created_at')
        if account.salesrep_set.exists():
            account = account
        else:
            assign_salesrep(account)
            

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


def get_token():
    try:
        response = requests.post("https://api.thecut.co/v1/auth/token", headers={
            "Authorization": "Basic YzgwMWE2NmEtNDJlMC00ZTZhLThiZTMtOTIwYzExNWY4NWJkOjU1NTM0MTFjLWIxNjMtNDYyNi1iYWU2LTk2YTczMjMzNzMyMQ==",
            "Auth-Client-Version": "1.25.1",
            "Device-Name": "Tm9raWEgQzMy",
            "Installation-Id": "17E229B5-41B7-4F4D-B44A-C76559665E54",
            "Device-Operating-System": "TIRAMISU (33)",
            "Device-Model": "Nokia Nokia C32",
            "Auth-Client-Name": "android-app",
            "Device-Fingerprint": "3a3f05ba6c66de6a",
            "Device-Platform": "android",
            "Signature": "v1 MTcwODMyNTg5NjpKSjltTUVSZjNmMXhtMUNLWHEzOHR1U0RUdDQxQmNpYTo4V09jZTUrS0dNa21ZR0doSGNmbmlxVlR1R0RFbmZIUkRSd1h0RXJua0FzPQ==",
            "Content-Type": "application/json; charset=utf-8",
            "Content-Length": "77",
            "Host": "api.thecut.co",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "User-Agent": "okhttp/4.11.0"
        }, json={
            "grant_type": "password",
            "username": "surgbc@gmail.com",
            "password": "ca!kacut"
        })
        data = response.json()
        return data["access_token"]
    except Exception as e:
        print("Error fetching access token:", e)
        raise e

def get_the_cut_info(thecut_username):
    access_token = get_token()
    response = requests.get(f"https://api.thecut.co/v2/barbers/{thecut_username}",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Auth-Client-Version": "1.25.1",
        "Device-Name": "Tm9raWEgQzMy",
        "Installation-Id": "17E229B5-41B7-4F4D-B44A-C76559665E54",
        "Device-Operating-System": "TIRAMISU (33)",
        "Device-Model": "Nokia Nokia C32",
        "Auth-Client-Name": "android-app",
        "Device-Fingerprint": "3a3f05ba6c66de6a",
        "Session-Id": "f822af9b4e3a61e0d5b71eacbca9c5a686fba9d2b968792e729a6138f4fde7e8122528f7230406f75ed335f6b822c732",
        "Device-Platform": "android",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Id": "65d2df444fd2435e639c4b43",
        "Signature": "v1 MTcwODMzNTg5NzprTFVKNmxjNFpiUzU4aXdUTFFsTENWQTFWNUlGSVFLMDpLQlhiand2bVpCeFppZmZieGFtYnd5bzh6aWp3c3FpSUU4ZHd6azViRHRrPQ=="
    })
    return response.json()
