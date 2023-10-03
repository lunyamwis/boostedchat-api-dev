import uuid
import re
from datetime import datetime, timezone
from celery import shared_task
from dialogflow.models import InstaLead, InstaMessage
from dialogflow.serializers import InstagramMessageSerializer
from dialogflow.helpers.intents import detect_intent

from instagram.helpers.login import login_user
from instagram.models import Account, Thread, Message
from dialogflow.prompt import get_prompt
from instagram.helpers.llm import query_gpt
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
def send_message(message, thread_id=None, user_id=None, username=None, thread=True):
    cl = login_user()
    user_id = None
    print("<<<<<<<<<<message<<<<<<<<<")
    print(message)
    print("<<<<<<<<<<username<<<<<<<<<")
    print(username)

    if username:
        user_id = cl.user_id_from_username(username)
        print("<<<<<<<<<<userid<<<<<<<<<")
        print(user_id)
        try:
            account = Account.objects.get(igname=username)
        except Exception as error:
            print(error)
        if type(user_id) == list:

            message = cl.direct_send(message, user_ids=user_id)
            thread = Thread()
            thread.thread_id = message.thread_id
            thread.account = account
            thread.save()
        elif type(user_id) == str:
            message = cl.direct_send(message, user_ids=[user_id])
            thread = Thread()
            thread.thread_id = message.thread_id
            thread.account = account
            thread.save()

    if thread_id and thread:
        if type(thread_id) == list:
            message = cl.direct_send(message, thread_ids=thread_id)
            print(message.text)
        elif type(thread_id) == str:
            message = cl.direct_send(message, thread_ids=[thread_id])
            print(message.text)


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
        saved_messages_arr = Message.objects.filter(thread__thread_id=thread_.thread_id).order_by("-sent_on")
        try:
            
            message = Message()
            if not saved_messages_arr.exists():
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
                    account_id=thread_.account.id
                )

                send_message.delay(
                    " ".join(map(str,generated_response)),
                    thread_id=thread_.thread_id,
                )
            if instagrapi_messages[0].timestamp == saved_messages_arr[0].sent_on:
                print("Bypassed")
                continue
            for instagrapi_message in instagrapi_messages:
                print(instagrapi_message.timestamp)
                print(saved_messages_arr[0].sent_on)
                if instagrapi_message.timestamp != saved_messages_arr[0].sent_on:
                    username = cl.username_from_user_id(instagrapi_message.user_id)

                    sent_by = "Robot"
                    if username == thread_.account.igname:
                        sent_by = "Client"
                    message.content = instagrapi_message.text
                    message.sent_by = sent_by
                    message.sent_on = instagrapi_message.timestamp
                    message.thread = thread_
                    message.save()
                else:
                    break

            generated_response = detect_intent(
                project_id="boostedchatapi",
                session_id=str(uuid .uuid4()),
                message=instagrapi_messages[0].text,
                language_code="en",
                account_id=thread_.account.id
            )
            print(generated_response)
            print(" ".join(map(str, generated_response)))

            send_message.delay(
                " ".join(map(str, generated_response)),
                thread_id=thread_.thread_id,
            )
        except Exception as error:
            print(error)


@shared_task()
def send_human_insta_message(message, username=None):
    cl = login_user()
    user_id = None

    if username:
        user_id = cl.user_id_from_username(username)
        if type(user_id) == list:
            cl.direct_send(message, user_ids=user_id)
        elif type(user_id) == str:
            cl.direct_send(message, user_ids=[user_id])
        elif type(user_id) == int:
            cl.direct_send(message, user_ids=[user_id])


@shared_task()
def send_and_save_insta_message(message_content, lead_id):
    cl = login_user()
    lead_obj = None
    try:
        lead_obj = InstaLead.objects.get(pk=lead_id)
    except InstaLead.DoesNotExist:
        pass
    user_id = cl.user_id_from_username(lead_obj.igname)
    message = None
    if type(user_id) == list:
        message = cl.direct_send(message_content, user_ids=user_id)
    elif type(user_id) == str:
        message = cl.direct_send(message_content, user_ids=[user_id])
    elif type(user_id) == int:
        message = cl.direct_send(message_content, user_ids=[user_id])

    lead_thread_id = message.thread_id
    lead_obj.thread_id = lead_thread_id
    lead_obj.save()

    message_data = {
        "content": message_content,
        "lead_id": lead_id,
        "sent_by": "Robot",
        "sent_on": datetime.now(timezone.utc)
    }

    serializer = InstagramMessageSerializer(data=message_data)
    if serializer.is_valid():
        serializer.save()


@shared_task()
def check_new_messages():
    cl = login_user()
    leads = InstaLead.objects.exclude(thread_id=None)
    for lead in leads:
        lead_thread_id = lead.thread_id
        lead_saved_messages = InstaMessage.objects.filter(lead_id=lead.id).order_by("-sent_on")
        lead_messages = cl.direct_messages(thread_id=lead_thread_id)

        if lead_messages[0].text != lead_saved_messages[0].content:
            username = cl.username_from_user_id(lead_messages[0].user_id)
            sent_by = "Robot"
            if username == lead.igname:
                sent_by = "Lead"
            message_data = {
                "content": lead_messages[0].text,
                "lead_id": lead.lead_id,
                "sent_by": sent_by,
                "sent_on": datetime.now(timezone.utc)
            }

            serializer = InstagramMessageSerializer(data=message_data)
            if serializer.is_valid():
                serializer.save()
            if sent_by == "Lead":
                send_gpt_message(lead=lead, lead_saved_messages=lead_saved_messages,
                                 respondent_message=lead_messages[0].text, cl=None)


def simulate_check_new_messages(respondent_message, lead: InstaLead):

    message_data = {
        "content": respondent_message,
        "lead_id": lead.id,
        "sent_by": "Lead",
        "sent_on": datetime.now(timezone.utc)
    }

    lead_saved_messages = InstaMessage.objects.filter(lead_id=lead.id).order_by("-sent_on")
    send_gpt_message(lead=lead, lead_saved_messages=lead_saved_messages,
                     respondent_message=respondent_message, cl=None)
    serializer = InstagramMessageSerializer(data=message_data)
    if serializer.is_valid():
        serializer.save()


def send_gpt_message(lead: InstaLead, lead_saved_messages, respondent_message, cl):

    formatted_messages = []
    for message in lead_saved_messages:
        formatted_message = ""
        if message.sent_by == "Lead":
            formatted_message = f"Respondent: {message.content}"
        else:
            formatted_message = f"You: {message.content}"
        formatted_messages.append(formatted_message)
    formatted_messages.append(f"Respondent: {respondent_message}")

    conversation_so_far = "\n".join(list(reversed(formatted_messages)))
    gpt_prompt = get_prompt(lead.status, conversation_so_far=conversation_so_far)
    response = query_gpt(gpt_prompt)
    result = response.get("choices")[0].get("message").get("content")

    gpt_generated_message = result.strip("\n")
    if (lead.status == 1):
        verify_move_to_needs_assessment(gpt_generated_message, lead, cl)
    elif lead.status == 2:
        verify_move_to_overcoming_objections(gpt_generated_message, lead, conversation_so_far, cl)
    # notice there is no third status as leads can never stay in sending solution to problems for more than a few seconds
    elif (lead.status == 4):
        verify_move_to_activation(gpt_generated_message, lead, cl)


def verify_move_to_needs_assessment(gpt_generated_message, lead: InstaLead, cl):
    """Lead is currently in the compliments phase(status 1). 
    We are inspecting the gpt response to find out if the LLM
    asked the question, "What is the most frustrating part of
    your barber gig?"
    """
    asked_first_question_re = re.findall(r'```(.*?)```', gpt_generated_message)

    send_and_save_insta_message_overload(gpt_generated_message, lead, cl)
    if len(asked_first_question_re) > 0 and asked_first_question_re[0] == "SENT-QUESTION":
        lead.status = 2
        lead.save()


def verify_move_to_overcoming_objections(gpt_generated_message, lead: InstaLead, conversation_so_far, cl):
    """Lead is currently in the needs assessment phase(status 2). 
    We are inspecting the gpt response to find out if the lead confirmed two or more problems
    """

    confirmed_rejected_problems_arr = re.findall(r"\+\+(.*?)\+\+", gpt_generated_message)
    confirmation_counter = 0
    for problem in confirmed_rejected_problems_arr:
        if "confirmed" in problem:
            confirmation_counter += 1

    if confirmation_counter >= 2:
        # Temporarily save them in sending solution to objections
        lead.status = 3
        lead.save()

        gpt_prompt = get_prompt(3, conversation_so_far=conversation_so_far)
        response = query_gpt(gpt_prompt)

        result = response.get("choices")[0].get("message").get("content")

        solution_presentation_message = result.strip("\n")
        send_and_save_insta_message_overload(solution_presentation_message, lead, cl)
        # Once solution has been sent, save them in resolving objections status
        lead.status = 4
        lead.save()
    else:
        llm_response = re.findall(r"\_\_\_\_(.*?)\_\_\_\_", gpt_generated_message)

        if len(llm_response) == 0:
            llm_response = re.findall(r"\_\_(.*?)\_\_", gpt_generated_message)
            if len(llm_response) == 0:
                llm_response = re.findall(r"\_(.*?)\_", gpt_generated_message)

        send_and_save_insta_message_overload(llm_response[0], lead, cl)


def verify_move_to_activation(gpt_generated_message, lead: InstaLead, cl):
    """Lead is currently in the resolving objections phase(status 4). 
    We are inspecting the gpt response to find out if the lead is interested
    """

    is_lead_interested = False
    objection_status_arr = re.findall(r'```(.*?)```', gpt_generated_message)
    for status in objection_status_arr:
        if status == "INTERESTED":
            is_lead_interested = True
            # send gpt message via instagram
    if is_lead_interested:
        """Client is interested. Move the to activating status"""
        lead.status = 5
        lead.save()
    else:
        """Most likely an objection, respond to the objection"""
        send_and_save_insta_message_overload(gpt_generated_message, lead, cl)


def send_and_save_insta_message_overload(message_content, lead: InstaLead, cl=None):
    # if cl is None:
    #   cl = login_user()

    # user_id = cl.user_id_from_username(lead)
    # message = None
    # if type(user_id) == list:
    #     message = cl.direct_send(message_content, user_ids=user_id)
    # elif type(user_id) == str:
    #     message = cl.direct_send(message_content, user_ids=[user_id])
    # elif type(user_id) == int:
    #     message = cl.direct_send(message_content, user_ids=[user_id])

    # lead_thread_id = message.thread_id
    lead_thread_id = "simulated"
    lead.thread_id = lead_thread_id
    lead.save()

    message_data = {
        "content": message_content,
        "lead_id": lead.id,
        "sent_by": "Robot",
        "sent_on": datetime.now(timezone.utc)
    }

    serializer = InstagramMessageSerializer(data=message_data)
    if serializer.is_valid():
        serializer.save()
