import logging
import os
import re

import requests
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from instagram.helpers.llm import query_gpt
from instagram.models import Account, Message, Thread


class FallbackWebhook(APIView):
    """
    List all snippets, or create a new snippet.
    """

    def post(self, request, format=None):

        convo = []
        thread = Thread()

        try:
            req = request.data
            query_result = req.get("fulfillmentInfo")

            query = req.get("text")

            account_id = req.get("payload").get("account_id")

            if query_result.get("tag") == "fallback":
                account = Account.objects.get(id=account_id)
                thread = Thread.objects.filter(account=account).last()
                url = os.getenv("SCRIPTING_URL")
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
