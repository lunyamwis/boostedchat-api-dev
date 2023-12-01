import datetime
import json
import logging

import requests
from celery import shared_task
from django.conf import settings
from django_celery_beat.models import PeriodicTask

from instagram.models import Account, Message, OutSourced, StatusCheck, Thread
from dialogflow.helpers.get_prompt_responses import get_gpt_response

from .helpers.format_username import format_full_name


@shared_task()
def send_first_compliment(username):
    print(username)
    thread_obj = None

    account = None
    try:
        account = Account.objects.get(igname="".join(username))
    except Exception as error:
        print(error)

    full_name = "there"
    try:
        full_name = format_full_name(account.full_name)
    except Exception as error:
        print(error)

    outsourced_data = OutSourced.objects.filter(account=account)

    
    first_message = get_gpt_response(account)
    
    media_id = outsourced_data.last().results.get("media_id", "")
    data = {"message": first_message.get('text'), "username": account.igname, "mediaId": media_id}

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
        raise Exception("There is something wrong with mqtt")
