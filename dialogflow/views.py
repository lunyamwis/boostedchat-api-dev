import os
import requests
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
                url = os.getenv("SCRIPT_URL")
                payload = {
                    "prompt_index": account.index,
                    "company_index": os.getenv("COMPANY_INDEX"),
                }
                response = requests.post(url, data=payload)
                prompt = response.get("prompt")
                steps = int(response.get("steps"))


                client_message = Message()
                client_message.content = query
                client_message.sent_by = "Client"
                client_message.sent_on = timezone.now()
                client_message.thread = thread
                client_message.save()


                prompt = ("\n").join(convo)
                response = query_gpt(prompt)

                result = response.get("choices")[0].get("message").get("content")
                completed = re.findall(r"```(.*?)```", result)
                if completed and account.index <= steps:
                    account.index = account.index + 1
                    account.save()

                result = result.strip("\n")
                robot_message = Message()
                robot_message.content = result
                robot_message.sent_by = "Robot"
                robot_message.sent_on = timezone.now()
                robot_message.thread = thread
                robot_message.save()


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
