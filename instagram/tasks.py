import datetime
import json
import logging
import time
import random

import requests
from celery import shared_task
from django.conf import settings
from django_celery_beat.models import PeriodicTask
from django.shortcuts import get_object_or_404

from instagram.models import Account, Message, OutSourced, StatusCheck, Thread
from sales_rep.models import SalesRep
from dialogflow.helpers.get_prompt_responses import get_gpt_response

from .helpers.format_username import format_full_name
from outreaches.views import process_reschedule_single_task

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

def sales_rep_is_logged_in(account, repeat = True):
    salesrep = account.salesrep_set.first()
    ig_username = salesrep.ig_username
    response = requests.get(settings.MQTT_BASE_URL + "/accounts")
    if response.status_code == 200:
        account_list = response.json()

        # Check if ig_username is in the response JSON
        if ig_username in account_list:
            # Process the response data further if needed
            pass
        else:
            if repeat:
                reschedule_last_enabled()
            # else:
            #     return # failing but repeat = False


            raise Exception(f"The Instagram username '{ig_username}' is not logged in in mqtt.") # this particular task has failed
    
    else: 
        raise Exception(f"There is something wrong with mqtt: {response}")

def reschedule_last_enabled():
    task = PeriodicTask.objects.filter(task="instagram.tasks.send_first_compliment", enabled=True).order_by('start_time').last()
    if task:
        current_time = datetime.datetime.now()
        task_time = current_time + datetime.timedelta(minutes=1)  # Add 1 minute to the current time
        start_hour = task_time.hour
        start_minute = task_time.minute
        process_reschedule_single_task("instagram.tasks.send_first_compliment", task.name, start_hour, start_minute, 48*3)
    else:
        print ('No more enabled tasks found')
    

@shared_task()
def send_first_compliment(username, repeat=True):
    print(username)
    thread_obj = None
    account = get_account(username)

    if account is None:
        print("Account does not exist")
        return

    # check if sales_rep is logged_in
    sales_rep_is_logged_in(account)

    # full_name = "there"
    # print(f'Account: {account}')
    # try:
    #     full_name = format_full_name(account.full_name)
    # except Exception as error:
    #     print(error)
    

    outsourced_data = OutSourced.objects.filter(account=account)

    salesrep = account.salesrep_set.first()
    first_message = get_gpt_response(account)

    media_id = outsourced_data.last().results.get("media_id", "")
    data = {"username_from":salesrep.ig_username,"message": first_message.get('text'), "username_to": account.igname, "mediaId": media_id}

    print(f"data=============={data}")
    print(f"data=============={json.dumps(data)}")
    response = requests.post(settings.MQTT_BASE_URL + "/send-first-media-message", data=json.dumps(data))
    if response.status_code == 200:
        print(f"actually worked for --------------- {account.igname}")
        sent_compliment_status = StatusCheck.objects.get(name="sent_compliment")
        account.status = sent_compliment_status
        account.save()
        print(f"response============{response}")
        try:

            print(f"json======================{response.json()}")
            returned_data = response.json()

            try:
                thread_obj, _ = Thread.objects.get_or_create(thread_id=returned_data["thread_id"])
            except Exception as error:
                print(error)
                try:
                    thread_obj = Thread.objects.get(thread_id=returned_data["thread_id"])
                except Exception as error:
                    print(error)
            thread_obj.thread_id = returned_data["thread_id"]
            thread_obj.account = account
            thread_obj.last_message_content = first_message.get('text')
            thread_obj.unread_message_count = 0
            thread_obj.last_message_at = datetime.datetime.fromtimestamp(int(returned_data['timestamp'])/1000000)
            thread_obj.save()

            message = Message()
            message.content = first_message.get('text')
            message.sent_by = "Robot"
            message.sent_on = datetime.datetime.fromtimestamp(int(returned_data["timestamp"]) / 1000000)
            message.thread = thread_obj
            message.save()
            try:
                PeriodicTask.objects.get(name=f"SendFirstCompliment-{account.igname}").delete()
            except Exception as error:
                logging.warning(error)
        except Exception as error:
            print(error)
            print("message not saved")

    else:
        # get last account in queue
        # delay 2 minutes
        # send  
        reschedule_last_enabled()

        raise Exception("There is something wrong with mqtt")
