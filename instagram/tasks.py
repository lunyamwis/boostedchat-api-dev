import datetime
import json
import logging

import requests
from celery import shared_task
from django.conf import settings
from django_celery_beat.models import PeriodicTask

from instagram.models import Account, Message, OutSourced, StatusCheck, Thread

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

    first_message = f"""Hey {full_name}, IG threw your profile my way — love
                        what you're doing with those shears!
                        I've been helping barbers up their marketing game a bit.
                        Got a few ideas that might be up your alley. Open to some tips?"""
    media_id = outsourced_data.last().results.get("media_id", "")
    data = {"message": first_message, "username": account.igname, "media_id": media_id}

    print(f"data=============={data}")
    print(f"data=============={json.dumps(data)}")
    response = requests.post(settings.MQTT_BASE_URL + "/send-first-media-message", data=json.dumps(data))
    if response.status_code == 200:
        print(f"actually worked for --------------- {account.igname}")
        sent_compliment_status = StatusCheck.objects.get(name="sent_compliment")
        account.status = sent_compliment_status
        account.save()
        print(f"response============{response}")
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
        message.content = first_message
        message.sent_by = "Robot"
        message.sent_on = datetime.datetime.fromtimestamp(int(returned_data["timestamp"]) / 1000000)
        message.thread = thread_obj
        message.save()
        try:
            PeriodicTask.objects.get(name=f"SendFirstCompliment-{account.igname}").delete()
        except Exception as error:
            logging.warning(error)

    else:
        raise Exception("There is something wrong with mqtt")
