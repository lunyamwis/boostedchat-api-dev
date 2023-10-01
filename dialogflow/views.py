from datetime import datetime
import json
import logging
import re
import uuid
from django.utils import timezone

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from dialogflow.models import InstaLead, InstaMessage
from dialogflow.serializers import InstagramMessageSerializer, CreateLeadSerializer, GetInstagramMessageSerializer, InstagramMessageSerializer

from instagram.helpers.llm import query_gpt
from instagram.models import Account, StatusCheck, Thread
from instagram.tasks import send_human_insta_message, send_and_save_insta_message, simulate_check_new_messages, send_and_save_insta_message_overload
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from .prompt import get_prompt


class FallbackWebhook(APIView):
    """
    List all snippets, or create a new snippet.
    """

    def post(self, request, format=None):

        # Possibly relevant information about the person you talk to & their business that you can use:
        # [relevant scraped data]
        convo = []
        # status_number = None
        statuscheck = None
        thread = Thread()
        account = Account.objects.first()
        thread.account = account
        # thread.thread_id = "340282366841710301244276027871564125912"
        # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        # print(request.session.items())
        # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

        # response = HttpResponse("Setting")
        # request.session["run_once"] = 1
        # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        # print(request.session.items())
        # print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        # status_prompt = f"""
        #     Categorize the following statuses and match the
        #     following dm within the triple backticks ```{request.data.get('text')}``` with the
        #     right status below from
        #     the following list of statuses
        #     0. sounds like anything outside the topics mentioned below or sounds like
        #     acknowledgement of a compliment
        #     1. sounds like an answer to 'What is the most frustrating part of your
        #     barber gig?' or indication of a
        #     problem not mentioned in the other points
        #     2. sounds like an answer to 'What is more important between managing
        #     current clients and attracting new
        #     ones?'
        #     3. sounds like an answer to 'How do you manage your calendar?' or
        #     'What is your [barber] booking system?'
        #     Do not match it to more than one status just simply give me something
        #     sensible based on the statuses that
        #     I have given you!
        #     Return the status number in double backticks!
        #     Always return a status number!!
        # """
        # state = query_gpt(status_prompt)
        # status_number = get_status_number(state.get("choices")[0].get("message").get("content"))

        statuschecks = StatusCheck.objects.filter(stage=2)
        if statuschecks.exists():
            statuscheck = statuschecks.last()

        # after_response = CheckResponse(status="confirmed_problem", thread=thread)
        print(statuscheck.stage)
        try:
            req = request.data
            # logging.warn('request data', req)
            query_result = req.get("fulfillmentInfo")
            print(query_result)

            query = req.get("text")

            if query_result.get("tag") == "fallback":
                print(query)
                # convo.append("DM:" + query)
                if statuscheck.stage in range(0, 3):
                    if statuscheck.name == "sent_compliment":
                        convo.append(get_prompt(statuscheck.stage - 1, client_message=query))
                        print(get_prompt(statuscheck.stage - 1, client_message=query))
                    if statuscheck.name == "sent_first_question":
                        convo.append(get_prompt(statuscheck.stage, client_message=query))
                    if statuscheck.name == "confirmed_problem":
                        convo.append(get_prompt(statuscheck.stage + 1, client_message=query))
                    if statuscheck.name == "overcome_objections":
                        convo.append(get_prompt(statuscheck.stage + 2, client_message=query))
                elif statuscheck.stage == 3:
                    pass

                prompt = ("\n").join(convo)
                response = query_gpt(prompt)

                result = response.get("choices")[0].get("message").get("content")

                result = result.strip("\n")

                if statuscheck.name == "sent_first_question":
                    confirmed_rejected_problems_arr = re.findall(r"\+\+(.*?)\+\+", result)
                    confirmation_counter = 0
                    for problem in confirmed_rejected_problems_arr:
                        if "confirmed" in problem:
                            confirmation_counter += 1

                    if confirmation_counter >= 3:
                        statuscheck.name = "confirmed_problem"
                        statuscheck.save()
                    llm_response = re.findall(r"\_\_\_\_(.*?)\_\_\_\_", result)

                    if len(llm_response) == 0:
                        llm_response = re.findall(r"\_\_(.*?)\_\_", result)

                    answers_re = re.search(r"```(.*?)```", result, re.DOTALL)
                    answers = None
                    if answers_re:
                        answers = answers_re.group(1)
                    print("-----result start-----")
                    print(result)
                    print("-----result end-----")
                    print("--------------Confirmed and rejected problems start---------------")
                    print(confirmed_rejected_problems_arr)
                    print("--------------Confirmed and rejected problems end---------------")
                    print("--------------answers start---------------")
                    print(answers)
                    print("--------------answers end---------------")
                    print("--------------response start---------------")
                    print(llm_response)
                    print("--------------response end---------------")
                    convo.append(result)

                    thread.content = f"{query},{llm_response[0]}"
                    thread.robot_response = llm_response[0]
                    thread.save()

                    return Response(
                        {
                            "fulfillment_response": {
                                "messages": [
                                    {
                                        "text": {
                                            "text": [llm_response[0]],
                                        },
                                    },
                                ]
                            }
                        },
                        status=status.HTTP_200_OK,
                    )

                if statuscheck.name == "confirmed_problem":
                    thread.content = query
                    thread.robot_response = result
                    return Response(
                        {
                            "fulfillment_response": {
                                "messages": [
                                    {
                                        "text": {
                                            "text": [result],
                                        },
                                    },
                                ]
                            }
                        },
                        status=status.HTTP_200_OK,
                    )

                if statuscheck.name == "overcome_objections":
                    matches_within_backticks = re.findall(r"```(.*?)```", result, re.DOTALL)
                    print(matches_within_backticks)
                    for objection in matches_within_backticks:
                        if "OVERCAME".upper() in objection:
                            statuscheck.name = "overcome"
                        if "DEFERRED".upper() in objection:
                            statuscheck.name = "deferred"

                        statuscheck.save()

                    matches_not_within_backticks = re.findall(r"(?<!```)([^`]+)(?!```)", result, re.DOTALL)
                    print(matches_not_within_backticks)
                    account.status = statuscheck
                    account.save()
                    thread.content = query
                    thread.robot_response = matches_not_within_backticks[-1]
                    return Response(
                        {
                            "fulfillment_response": {
                                "messages": [
                                    {
                                        "text": {
                                            "text": [matches_not_within_backticks[-1]],
                                        },
                                    },
                                ]
                            }
                        },
                        status=status.HTTP_200_OK,
                    )
        except Exception as error:
            print(error)


class NeedsAssesmentWebhook(APIView):
    """
    List all snippets, or create a new snippet.
    """

    def post(self, request, format=None):

        convo = []
        try:
            req = request.data
            # logging.warn('request data', req)
            query_result = req.get("fulfillmentInfo")
            print(query_result)
            query = req.get("text")
            # import pdb;pdb.set_trace()
            if query_result.get("tag") == "firstquestion":
                print(query)
                convo.append("DM:" + query)
                # convo.append(prompts.get("NA"))
                # prompt = ("\n").join(convo)
                # logging.warn('prompt so far', convo)
                # response = query_gpt(prompt)

                # logging.warn('gpt resp', response)
                # result = response.get("choices")[0].get("message").get("content")
                result = "What is the gnarliest part of your barber gig?"
                result = result.strip("\n")
                logging.warn(result)
                convo.append(result)
                logging.warn(str(["convo so far", ("\n").join(convo)]))
                return Response(
                    {
                        "fulfillment_response": {
                            "messages": [
                                {
                                    "text": {
                                        "text": [result],
                                    },
                                },
                            ]
                        }
                    },
                    status=status.HTTP_200_OK,
                )

        except Exception as error:
            print(error)


@api_view(['POST'])
def create_lead(request):
    """Creates a lead without sending the first compliment"""
    serializer = CreateLeadSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({"errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
def update_lead(request, leadId):
    """Updates a lead"""
    try:
        lead = InstaLead.objects.get(id=leadId)
    except InstaLead.DoesNotExist:
        return Response({"message": "Lead does not exist"}, status=status.HTTP_201_CREATED)

    serializer = CreateLeadSerializer(lead, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({"errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
def start_lead_engagement(request, leadId):
    try:
        lead = InstaLead.objects.get(id=leadId)
        compliment_prompt = get_prompt(1, conversation_so_far="")

        response = query_gpt(compliment_prompt)

        result = response.get("choices")[0].get("message").get("content")

        result = result.strip("\n")

        send_and_save_insta_message_overload(result, lead)
        lead.is_engaged = True
        lead.save()
        return Response({"message": "Engagement started successfully"}, status=status.HTTP_201_CREATED)
    except InstaLead.DoesNotExist:
        return Response({"message": "Lead does not exist"}, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
def delete_lead(request):
    try:
        lead = InstaLead.objects.get(igname=request.data.get("igname"))
        lead.delete()
        return Response({"message": "Lead deleted successfully"}, status=status.HTTP_201_CREATED)
    except InstaLead.DoesNotExist:
        return Response({"message": "Lead does not exist"}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def create_lead_and_send_compliment(request):
    compliment_prompt = get_prompt(1, client_message="")

    response = query_gpt(compliment_prompt)

    result = response.get("choices")[0].get("message").get("content")

    result = result.strip("\n")

    create_data = {**request.data, **{"id": uuid.uuid4(), "is_engaged": True}}
    serializer = CreateLeadSerializer(data=create_data)
    if serializer.is_valid():
        serializer.save()
        send_and_save_insta_message.delay(result, serializer.validated_data["id"])
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({"errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_leads(request):
    leads = InstaLead.objects.order_by('-updated_on')
    serializer = CreateLeadSerializer(leads, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def send_human_insta_message(request, leadId):
    content = request.data.get("content")
    if leadId is None or content is None:
        return Response({"message": "Please provide lead id and message content"},
                        status=status.HTTP_400_BAD_REQUEST)
    try:
        lead_obj = InstaLead.objects.get(pk=leadId)
    except InstaLead.DoesNotExist:
        return Response({"message": "Lead does not exist"}, status=status.HTTP_201_CREATED)

    send_human_insta_message.delay(content, lead_obj.igname)

    message_data = {
        "content": content,
        "lead_id": leadId,
        "sent_by": "Human",
        "sent_on": datetime.now()
    }

    serializer = InstagramMessageSerializer(data=message_data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({"errors": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def simulate_check_message(request):
    """Creates a lead without sending the first compliment"""
    lead_id = request.data.get('lead_id')

    try:
        lead = InstaLead.objects.get(id=lead_id)
        simulate_check_new_messages(request.data.get('message'), lead)
        return Response({"message": "Simulation success"}, status=status.HTTP_201_CREATED)
    except InstaLead.DoesNotExist:
        return Response({"message": "Lead does not exist"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
def delete_message(request, pk):
    try:
        message = InstaMessage.objects.get(id=pk)
        message.delete()
        return Response({"message": "Message deleted successfully"}, status=status.HTTP_200_OK)
    except InstaLead.DoesNotExist:
        return Response({"message": "Message does not exist"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_messages(request):
    messages = InstaMessage.objects.order_by('-sent_on')
    serializer = GetInstagramMessageSerializer(messages, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_messages_by_lead(request,leadId):
    messages = InstaMessage.objects.filter(lead_id=leadId).order_by('-sent_on')
    serializer = InstagramMessageSerializer(messages, many=True)
    return Response(serializer.data)


@api_view(["POST"])
def set_check_message_periodic_task(request):
    try:
        PeriodicTask.objects.get(name="CheckNewMessageCron")
        return Response({"message": "Periodic task already exists"}, status=status.HTTP_201_CREATED)
    except PeriodicTask.DoesNotExist:
        schedule = CrontabSchedule.objects.save(
            minute="*/5",
            hour="*",
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
        )
        PeriodicTask.objects.save(
            name="CheckNewMessageCron",
            crontab=schedule,
            task="instagram.tasks.check_new_message",
            args=json.dumps([[""], [""]]),
            start_time=timezone.now(),
        )
        return Response({"message": "Periodic task created successfully"}, status=status.HTTP_201_CREATED)


@api_view(["POST"])
def update_check_message_periodic_task(request):
    try:
        task = PeriodicTask.objects.get(name="CheckNewMessageCron")

        schedule = CrontabSchedule.objects.save(
            minute="*/5",
            hour="*",
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
        )
        task.crontab = schedule
        task.save()
        return Response({"message": "Periodic task updated successfully"}, status=status.HTTP_201_CREATED)
    except PeriodicTask.DoesNotExist:
        schedule = CrontabSchedule.objects.save(
            minute="*/5",
            hour="*",
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
        )
        PeriodicTask.objects.save(
            name="CheckNewMessageCron",
            crontab=schedule,
            task="instagram.tasks.check_new_message",
            args=json.dumps([[""], [""]]),
            start_time=timezone.now(),
        )
        return Response({"message": "Periodic task created successfully"}, status=status.HTTP_201_CREATED)
