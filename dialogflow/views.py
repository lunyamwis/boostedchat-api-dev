import json
import logging
import re
import uuid
from datetime import datetime

from django.utils import timezone
from django_celery_beat.models import CrontabSchedule, PeriodicTask
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from data.helpers.random_data import (
    get_matching_objection_response,
    get_matching_questions,
    get_matching_solutions,
    get_potential_problems,
)
from dialogflow.models import InstaLead, InstaMessage
from dialogflow.serializers import CreateLeadSerializer, GetInstagramMessageSerializer, InstagramMessageSerializer
from instagram.helpers.llm import query_gpt
from instagram.models import Account, Message, OutSourced, StatusCheck, Thread
from instagram.tasks import (
    send_and_save_insta_message,
    send_and_save_insta_message_overload,
    send_human_insta_message,
    simulate_check_new_messages,
)

from .prompt import get_first_prompt, get_prompt, get_second_prompt, get_third_prompt, get_fourth_prompt


class FallbackWebhook(APIView):
    """
    List all snippets, or create a new snippet.
    """

    def post(self, request, format=None):

        convo = []
        status_check = None
        thread = Thread()
        message = Message()

        try:
            req = request.data
            query_result = req.get("fulfillmentInfo")

            query = req.get("text")
            # account_id = req.get("payload").get("account_id")
            account_id = "-NeCzVITeCfyMeaZMaUw"
            if query_result.get("tag") == "fallback":
                account = Account.objects.get(id=account_id)
                thread = Thread.objects.get(account=account)

                outsourced_data = OutSourced.objects.filter(account=account).last()
                thread.account = account
                questions = get_matching_questions(
                    outsourced_data.results["calendar_availability"],
                    outsourced_data.results["booking_system"],
                    outsourced_data.results["sm_activity"],
                    outsourced_data.results["book_button"],
                )
                solutions = get_matching_solutions(
                    outsourced_data.results["calendar_availability"],
                    outsourced_data.results["booking_system"],
                    outsourced_data.results["sm_activity"],
                    outsourced_data.results["book_button"],
                )
                potential_problems = get_potential_problems(
                    outsourced_data.results["calendar_availability"],
                    outsourced_data.results["booking_system"],
                    outsourced_data.results["sm_activity"],
                    outsourced_data.results["book_button"],
                )
                objection_response = get_matching_objection_response(outsourced_data.source)
                booking_question = None
                if not outsourced_data.results["booking_system"]:
                    booking_question = f"""
                        - How do you manage your bookings? (If the respondent mentions
                        their booking platform, return the name of that platform, options include booking
                        systems and custom solutions like: "styleseat", "vagaro", "the cut", "acuity",
                        "dm or call to book", "squire", or other)

                        """
                calendar_availability_question = None
                if not outsourced_data.results["calendar_availability"]:
                    calendar_availability_question = f"""
                        - What's more important between managing
                        existing current clients and attracting new ones? (If the respondent talks about
                        their calendar needs, return the corresponding value depending on their focus:
                        "full calendar" if returning clients, "empty calendar" if new clients,
                        "some availability" if both)
                        """
                print(potential_problems)
                status_check = account.status
                print("<<>Status>>>")
                print(status_check)
                print(status_check.stage)
                print("<<>Status>>>")

                client_message = Message()
                client_message.content = query
                client_message.sent_by = "Client"
                client_message.sent_on = timezone.now()
                client_message.thread = thread
                client_message.save()
                # convo.append("DM:" + query)
                if status_check.stage in range(0, 4):
                    if status_check.name == "sent_compliment":
                        convo.append(get_first_prompt(conversation_so_far=get_conversation_so_far(thread.thread_id)))
                    if status_check.name == "sent_first_question":
                        convo.append(
                            get_second_prompt(
                                conversation_so_far=get_conversation_so_far(thread.thread_id),
                                booking_question=booking_question,
                                calendar_availability_question=calendar_availability_question,
                                questions=questions,
                                potential_problems=potential_problems,
                                generic_problems=objection_response,
                            )
                        )
                    if status_check.name == "confirmed_problem":
                        convo.append(
                            get_third_prompt(
                                conversation_so_far=get_conversation_so_far(thread.thread_id), solutions=solutions
                            )
                        )

                    print(status_check.name)
                    print(status_check.name == "overcome_objections")
                    if status_check.name == "overcome_objections":
                        print("<-----Prompt #4------->")
                        convo.append(
                            get_fourth_prompt(
                                conversation_so_far=get_conversation_so_far(thread.thread_id),
                                objection=objection_response,
                                objection_system=outsourced_data.source,
                                current_time=timezone.now(),
                            )
                        )
                elif status_check.stage == 3:
                    pass

                prompt = ("\n").join(convo)
                response = query_gpt(prompt)
                print(response)
                print("138")
                print(prompt)
                print("140")

                result = response.get("choices")[0].get("message").get("content")

                result = result.strip("\n")

                if status_check.name == "sent_compliment":
                    asked_first_question_re = re.findall(r"```(.*?)```", result)
                    # matches_not_within_backticks = re.findall(r"(?<!```)([^`]+)(?!```)", result, re.DOTALL)
                    robot_message = Message()
                    robot_message.content = result
                    robot_message.sent_by = "Robot"
                    robot_message.sent_on = timezone.now()
                    robot_message.thread = thread
                    robot_message.save()
                    if len(asked_first_question_re) > 0 and asked_first_question_re[0] == "SENT-QUESTION":
                        status_check.name = "sent_first_question"
                        status_check.stage = 2
                        status_check.save()
                        sent_first_question_status = StatusCheck.objects.filter(name="sent_first_question").last()

                        account.status = sent_first_question_status
                        account.save()
                        print(account)

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

                if status_check.name == "sent_first_question":
                    confirmed_rejected_problems_arr = re.findall(r"\+\+(.*?)\+\+", result)
                    confirmation_counter = 0
                    for problem in confirmed_rejected_problems_arr:
                        if "confirmed" in problem:
                            confirmation_counter += 1

                    if confirmation_counter >= 3:
                        status_check.name = "confirmed_problem"
                        status_check.stage = 2
                        status_check.save()
                        confirmed_problem_status = StatusCheck.objects.filter(name="confirmed_problem").last()
                        account.status = confirmed_problem_status
                        account.save()
                    try:
                        llm_response = re.findall(r"\_\_\_\_(.*?)\_\_\_\_", result)
                    except Exception as error:
                        try:
                            llm_response = re.findall(r'____\n(.*?)\n____', result, re.DOTALL)
                        except Exception as error:
                            print(error)

                    if len(llm_response) == 0:
                        llm_response = re.findall(r"\_\_(.*?)\_\_", result)
                    if "" in llm_response:
                        llm_response = re.findall(r'____\n(.*?)\n____', result, re.DOTALL)
                    if len(llm_response) == 0:
                        llm_response = re.findall(r'\n_(.*?)\_', result, re.DOTALL)


                    answers_re = re.search(r"```(.*?)```", result, re.DOTALL)
                    answers = None
                    if answers_re:
                        answers = answers_re.group(1)
                    convo.append(result)

                    try:
                        print("<<<try>>")
                        print(llm_response)
                        print("<<<try>>")
                        message.content = llm_response[0]
                        message.sent_by = "Robot"
                        message.sent_on = timezone.now()
                        message.thread = thread
                        message.save()
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
                    except Exception as error:
                        print("<<<err>>")
                        print(llm_response)
                        print("<<<err>>")
                        message.content = llm_response
                        message.sent_by = "Robot"
                        message.sent_on = timezone.now()
                        message.thread = thread
                        message.save()
                        return Response(
                            {
                                "fulfillment_response": {
                                    "messages": [
                                        {
                                            "text": {
                                                "text": [llm_response],
                                            },
                                        },
                                    ]
                                }
                            },
                            status=status.HTTP_200_OK,
                        )

                if status_check.name == "confirmed_problem":
                    message.content = result
                    message.sent_by = "Robot"
                    message.sent_on = timezone.now()
                    message.thread = thread
                    message.save()
                    status_check.name = "overcome_objections"
                    status_check.stage = 3
                    status_check.save()
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

                if status_check.name == "overcome_objections":
                    matches_within_backticks = re.findall(r"```(.*?)```", result, re.DOTALL)
                    print(matches_within_backticks)
                    for objection in matches_within_backticks:
                        if "OVERCAME".upper() in objection:
                            status_check.name = "overcome"
                        if "DEFERRED".upper() in objection:
                            status_check.name = "deferred"

                        status_check.save()

                    matches_not_within_backticks = re.findall(r"(?<!```)([^`]+)(?!```)", result, re.DOTALL)
                    print(matches_not_within_backticks)
                    account.status = status_check
                    account.save()
                    message.content = matches_not_within_backticks[-1]
                    message.sent_by = "Robot"
                    message.sent_on = timezone.now()
                    message.thread = thread
                    message.save()
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

            return Response(
                {
                    "fulfillment_response": {
                        "messages": [
                            {
                                "text": {
                                    "text": ["Some text"],
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


@api_view(["POST"])
def create_lead(request):
    """Creates a lead without sending the first compliment"""
    serializer = CreateLeadSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PATCH"])
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
    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["PATCH"])
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


@api_view(["POST"])
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
    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def get_leads(request):
    leads = InstaLead.objects.order_by("-updated_on")
    serializer = CreateLeadSerializer(leads, many=True)
    return Response(serializer.data)


@api_view(["POST"])
def send_human_insta_message(request, leadId):
    content = request.data.get("content")
    if leadId is None or content is None:
        return Response({"message": "Please provide lead id and message content"}, status=status.HTTP_400_BAD_REQUEST)
    try:
        lead_obj = InstaLead.objects.get(pk=leadId)
    except InstaLead.DoesNotExist:
        return Response({"message": "Lead does not exist"}, status=status.HTTP_201_CREATED)

    send_human_insta_message.delay(content, lead_obj.igname)

    message_data = {"content": content, "lead_id": leadId, "sent_by": "Human", "sent_on": datetime.now()}

    serializer = InstagramMessageSerializer(data=message_data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(["POST"])
def simulate_check_message(request):
    """Creates a lead without sending the first compliment"""
    lead_id = request.data.get("lead_id")

    try:
        lead = InstaLead.objects.get(id=lead_id)
        simulate_check_new_messages(request.data.get("message"), lead)
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


@api_view(["GET"])
def get_messages(request):
    messages = InstaMessage.objects.order_by("-sent_on")
    serializer = GetInstagramMessageSerializer(messages, many=True)
    return Response(serializer.data)


@api_view(["GET"])
def get_messages_by_lead(request, leadId):
    messages = InstaMessage.objects.filter(lead_id=leadId).order_by("-sent_on")
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


def get_conversation_so_far(thread_id):
    messages = Message.objects.filter(thread=thread_id)
    formatted_messages = []
    for message in messages:
        formatted_message = ""
        if message.sent_by == "Client":
            formatted_message = f"Respondent: {message.content}"
        else:
            formatted_message = f"You: {message.content}"
        formatted_messages.append(formatted_message)
    return "\n".join(formatted_messages)
