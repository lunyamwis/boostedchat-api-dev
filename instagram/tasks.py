import re
import uuid
from datetime import datetime, timezone

from celery import shared_task
from django.db.models import Q

from dialogflow.helpers.intents import detect_intent
from instagram.helpers.login import login_user
from instagram.models import Account, Message, Thread

from .helpers.check_response import CheckResponse


@shared_task()
def send_comment(media_link, generated_response):
    cl = login_user()
    media_pk = cl.media_pk_from_url(media_link)
    media_id = cl.media_id(media_pk=media_pk)
    cl = login_user()
    cl.media_comment(media_id, generated_response)


@shared_task
def follow_user(username):
    cl = login_user()
    user_id = cl.user_id_from_username(username)
    cl.user_follow(user_id)


@shared_task()
def send_message(message_content, thread_id, sent_by="Robot"):
    thread = Thread.objects.get(thread_id=thread_id)
    cl = login_user()

    direct_message = cl.direct_send(message_content, thread_ids=[thread.thread_id])

    message = Message()
    message.content = message_content
    message.sent_by = sent_by
    message.sent_on = direct_message.timestamp
    message.thread = thread
    message.save()


@shared_task()
def send_first_compliment(username):
    cl = login_user()
    thread_obj = None
    first_message = f"Hey {username}, IG just suggested to me your account and I love your work! I can see that a few quick additions to the way you post on IG will get even more people to book you and I was wondering if you’re open to feedback?"

    user_id = cl.user_id_from_username(username)
    if type(user_id) != list:
        user_id = [user_id]

    account = None
    try:
        account = Account.objects.get(igname=username)
    except Exception as error:
        print(error)

    # cl.user_follow(user_id)
    direct_message = cl.direct_send(first_message, user_ids=user_id)
    try:
        thread_obj, _ = Thread.objects.get_or_create(thread_id=direct_message.thread_id)
    except Exception as error:
        try:
            thread_obj = Thread.objects.get(thread_id=direct_message.thread_id)
        except Exception as error:
            print(error)
    thread_obj.thread_id = direct_message.thread_id
    thread_obj.account = account
    thread_obj.save()

    message = Message()
    message.content = first_message
    message.sent_by = "Robot"
    message.sent_on = direct_message.timestamp
    message.thread = thread_obj
    message.save()


@shared_task()
def check_response():
    cl = login_user()

    for thread in Thread.objects.all():
        instagrapi_messages = cl.direct_messages(thread_id=thread.thread_id)
        saved_messages_arr = Message.objects.filter(
            Q(thread__thread_id=thread.thread_id) & Q(sent_by="Client")
        ).order_by("-sent_on")
        print(saved_messages_arr)
        check_response = CheckResponse(status=thread.account.status.name, thread=thread)
        try:

            username = cl.username_from_user_id(instagrapi_messages[0].user_id)
            print(username)
            if not saved_messages_arr.exists() and username == thread.account.igname:
                print("first_messages")
                check_response.follow_up_if_sent_first_compliment()
            if instagrapi_messages[0].text == saved_messages_arr[0].content and username == thread.account.igname:
                print("reached_here")
                if check_response.status == "overcome":
                    check_response.follow_up_after_presentation()
                    check_response.follow_up_if_sent_email_first_attempt()
                    check_response.follow_up_ready_switch()
                    check_response.follow_up_share_flyer()
                    check_response.follow_up_highest_impact_actions()
                    check_response.follow_up_greeting_day()
                    check_response.follow_up_after_4_weeks()
                    check_response.follow_up_after_4_weeks_2_days()
                    check_response.follow_up_get_clients()
                elif check_response.status == "deferred":
                    check_response.follow_up_if_deferred()

        except Exception as error:
            print(error)


@shared_task()
def generate_and_send_response():
    cl = login_user()

    for thread_ in Thread.objects.all():
        instagrapi_messages = cl.direct_messages(thread_id=thread_.thread_id)
        print(thread_)
        saved_messages_arr = Message.objects.filter(
            Q(thread__thread_id=thread_.thread_id) & Q(sent_by="Client")
        ).order_by("-sent_on")
        try:

            message = Message()
            username = cl.username_from_user_id(instagrapi_messages[0].user_id)
            print(username)
            if not saved_messages_arr.exists() and username == thread_.account.igname:

                message.content = instagrapi_messages[0].text
                message.sent_by = "Client"
                message.sent_on = instagrapi_messages[0].timestamp
                message.thread = thread_
                message.save()
                generated_response = detect_intent(
                    project_id="boostedchatapi",
                    session_id=str(uuid.uuid4()),
                    message=instagrapi_messages[0].text,
                    language_code="en",
                    account_id=thread_.account.id,
                )

                send_message.delay(
                    " ".join(map(str, generated_response)),
                    thread=thread_,
                )
            if instagrapi_messages[0].text == saved_messages_arr[0].content:
                print("Bypassed")
                continue

            if instagrapi_messages[0].text != saved_messages_arr[0].content and username == thread_.account.igname:
                generated_response = detect_intent(
                    project_id="boostedchatapi",
                    session_id=str(uuid.uuid4()),
                    message=instagrapi_messages[0].text,
                    language_code="en",
                    account_id=thread_.account.id,
                )
                print(generated_response)
                print(" ".join(map(str, generated_response)))

                send_message.delay(
                    " ".join(map(str, generated_response)),
                    thread=thread_,
                )


        except Exception as error:
            print(error)