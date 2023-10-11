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
def send_message(message_content, thread, sent_by="Robot"):
    print("thread")
    print(thread)
    print("Call send message")
    cl = login_user()

    direct_message = cl.direct_send(message_content, thread_ids=[thread.thread_id])

    message = Message()
    message.content = message_content
    message.sent_by = sent_by
    message.sent_on = direct_message.timestamp
    message.thread = thread
    message.save()


@shared_task()
def send_first_compliment(message_content, username):
    cl = login_user()
    thread_obj = None

    user_id = cl.user_id_from_username(username)
    if type(user_id) != list:
        user_id = [user_id]

    try:
        account = Account.objects.get(igname=username)
    except Exception as error:
        print(error)

    direct_message = cl.direct_send(message_content, user_ids=user_id)
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
    message.content = message_content
    message.sent_by = "Robot"
    message.sent_on = direct_message.timestamp
    message.thread = thread_obj
    message.save()


@shared_task()
def check_response():
    cl = login_user()

    for thread_ in Thread.objects.all():
        instagrapi_messages = cl.direct_messages(thread_id=thread_.thread_id)
        saved_messages_arr = Message.objects.filter(thread=thread_.thread_id).order_by("-sent_on")
        if instagrapi_messages[0].text != saved_messages_arr[0].content:
            for instagrapi_message in instagrapi_messages:
                if instagrapi_message != saved_messages_arr[0].content:
                    username = cl.username_from_user_id(instagrapi_message.user_id)

                    sent_by = "Robot"
                    if username == thread_.account.igname:
                        sent_by = "Client"
                    message = Message()
                    message.content = instagrapi_message.text
                    message.sent_by = sent_by
                    message.sent_on = instagrapi_message.timestamp
                    message.thread = thread_
                    message.save()
                else:
                    break
            continue

        check_responses = CheckResponse(status=thread_.account.status.name, thread=thread_)

        if check_responses.status == "responded_to_first_compliment":
            check_responses.follow_up_if_responded_to_first_compliment()
        elif check_responses.status == "sent_first_compliment":
            check_responses.follow_up_if_sent_first_compliment()
        elif check_responses.status == "sent_first_question":
            check_responses.follow_up_if_sent_first_question()
        elif check_responses.status == "sent_second_question":
            check_responses.follow_up_if_sent_second_question()
        elif check_responses.status == "sent_third_question":
            check_responses.follow_up_if_sent_third_question()
        elif check_responses.status == "sent_first_needs_assessment_question":
            check_responses.follow_up_if_sent_first_needs_assessment_question()
        elif check_responses.status == "sent_second_needs_assessment_question":
            check_responses.follow_up_if_sent_second_needs_assessment_question()
        elif check_responses.status == "sent_third_needs_assessment_question":
            check_responses.follow_up_if_sent_third_needs_assessment_question()
        elif check_responses.status == "sent_follow_up_after_presentation":
            check_responses.follow_up_after_presentation()
        elif check_responses.status == "sent_email_first_attempt":
            check_responses.follow_up_if_sent_email_first_attempt()
        elif check_responses.status == "sent_uninterest":
            check_responses.follow_up_if_sent_uninterest()
        elif check_responses.status == "sent_objection":
            check_responses.follow_up_if_sent_objection()
        elif check_responses.status == "overcome":
            check_responses.follow_up_after_solutions_presented()
            check_responses.follow_up_if_sent_email_first_attempt()
        elif check_responses.status == "deferred":
            check_responses.follow_up_if_deferred()


@shared_task()
def generate_and_send_response():
    cl = login_user()

    for thread_ in Thread.objects.all():
        instagrapi_messages = cl.direct_messages(thread_id=thread_.thread_id)
        
        client_user_id = cl.user_id_from_username(username=thread_.account.igname)


        saved_messages_arr = Message.objects.filter(
            Q(thread__thread_id=thread_.thread_id) & Q(sent_by="Client")
        ).order_by("-sent_on")

        try:

            message = Message()
            username = cl.username_from_user_id(instagrapi_messages[0].user_id)
            if username != thread_.account.igname:
                # Sender of last message is not the lead so move on to the next thread in next iteration
                continue
            if saved_messages_arr.exists():
                client_temp_messages = []
                for instagrapi_message in instagrapi_messages:
                    if instagrapi_message.text != saved_messages_arr[0].content:
                        if instagrapi_message.user_id == client_user_id:
                            client_temp_messages.append(instagrapi_message.text)
                        else:
                            message = Message()
                            message.content = instagrapi_message.text
                            message.sent_by = "Robot"
                            message.sent_on = instagrapi_message.timestamp
                            message.thread = thread_
                            message.save()

                if len(client_temp_messages) > 0:
                    generated_response = detect_intent(
                        project_id="boostedchatapi",
                        session_id=str(uuid.uuid4()),
                        message=". ".join(client_temp_messages),
                        language_code="en",
                        account_id=thread_.account.id,
                    )
                    print(generated_response)
                    print(" ".join(map(str, generated_response)))

                    send_message.delay(
                        " ".join(map(str, generated_response)),
                        thread=thread_,
                    )
            else:
                print("Messages do not exist and username is true")
                print(instagrapi_messages)
                print("Messages do not exist and username is true")
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
                print("Generated")
                print(generated_response)
                print("Generated")
                print(
                    " ".join(map(str, generated_response)),
                )

                send_message.delay(
                    " ".join(map(str, generated_response)),
                    thread=thread_,
                )


        except Exception as error:
            print(error)

