import logging
import re

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from data.helpers.random_data import (
    get_matching_objection_response,
    get_matching_questions,
    get_matching_solutions,
    get_potential_problems,
)
from dialogflow.helpers.conversations import get_conversation_so_far
from instagram.helpers.llm import query_gpt
from instagram.models import Account, Message, OutSourced, StatusCheck, Thread

from .prompt import get_first_prompt, get_fourth_prompt, get_second_prompt, get_third_prompt


class FallbackWebhook(APIView):
    """
    List all snippets, or create a new snippet.
    """

    def post(self, request, format=None):

        convo = []
        status_check = None
        thread = Thread()

        try:
            req = request.data
            query_result = req.get("fulfillmentInfo")

            query = req.get("text")

            account_id = req.get("payload").get("account_id")

            if query_result.get("tag") == "fallback":
                account = Account.objects.get(id=account_id)
                thread = Thread.objects.filter(account=account).last()

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
                                conversation_so_far=get_conversation_so_far(thread.thread_id),
                                confirmed_problems=account.confirmed_problems,
                                solutions=solutions,
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
                    print("<<<<<<<<<<<question>>>>>>>>>>>>>")
                    print(asked_first_question_re)
                    print("<<<<<<<<<<<question>>>>>>>>>>>>>")
                    # matches_not_within_backticks = re.findall(r"(?<!```)([^`]+)(?!```)", result, re.DOTALL)

                    robot_message = Message()
                    robot_message.content = result
                    robot_message.sent_by = "Robot"
                    robot_message.sent_on = timezone.now()
                    robot_message.thread = thread
                    robot_message.save()
                    if len(asked_first_question_re) > 0 and asked_first_question_re[0] == "QUESTION SHARED":
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
                                            "text": [result.replace("```QUESTION SHARED```", "")],
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
                    # for problem in confirmed_rejected_problems_arr:
                    #     if "confirmed" in problem:
                    #         list_conf_pr = problem.split(",")
                    #         if len(list_conf_pr) == 3:
                    #             confirmation_counter = 3

                    for problem in confirmed_rejected_problems_arr:
                        if "confirmed" in problem:
                            confirmation_counter += 1

                    if confirmation_counter >= 2:
                        confirmed_problem_status = StatusCheck.objects.filter(name="confirmed_problem").last()
                        problems = re.findall(r"```(.*?)```", result, re.DOTALL)
                        account.confirmed_problems = [
                            problem for problem in confirmed_rejected_problems_arr if "confirmed" in problem
                        ]
                        account.rejected_problems = [
                            problem for problem in confirmed_rejected_problems_arr if "rejected" in problem
                        ]
                        account.status = confirmed_problem_status
                        account.save()

                    matched_string = result.replace("".join(confirmed_rejected_problems_arr), "")
                    llm_response = re.sub(r"[(+*)]", "", matched_string)

                    answers_re = re.search(r"```(.*?)```", result, re.DOTALL)
                    answers = None
                    if answers_re:
                        answers = answers_re.group(1)
                    convo.append(result)

                    try:
                        print("<<<try>>")
                        print(llm_response)
                        print("<<<try>>")

                        message = Message()
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
                    except Exception as error:
                        print("<<<err>>")
                        print(llm_response)
                        print("<<<err>>")

                        message = Message()
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

                    message = Message()
                    message.content = result
                    message.sent_by = "Robot"
                    message.sent_on = timezone.now()
                    message.thread = thread
                    message.save()

                    overcome_objection_status = StatusCheck.objects.filter(name="overcome_objections").last()
                    account.status = overcome_objection_status
                    account.save()
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
                            overcome_status = StatusCheck.objects.filter(name="overcome").last()
                            account.status = overcome_status
                        if "DEFERRED".upper() in objection:
                            deferred_status = StatusCheck.objects.filter(name="deferred").last()
                            account.status = deferred_status

                        account.save()

                    matches_not_within_backticks = result.replace("```", "")
                    print(matches_not_within_backticks)
                    account.status = status_check
                    account.save()

                    message = Message()
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
                                            "text": [
                                                matches_not_within_backticks.replace(
                                                    "\n".join(matches_within_backticks), ""
                                                )
                                            ],
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
            logging.warn(error)
            return Response(
                {
                    "fulfillment_response": {
                        "messages": [
                            {
                                "text": {
                                    "text": ["Come again"],
                                },
                            },
                        ]
                    }
                },
                status=status.HTTP_200_OK,
            )


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
