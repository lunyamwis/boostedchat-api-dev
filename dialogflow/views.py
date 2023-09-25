import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from instagram.helpers.llm import query_gpt
from instagram.models import StatusCheck

from .helpers.get_status_number import get_status_number
from .models import RequestTracker
from .prompt import prompts


class FallbackWebhook(APIView):
    """
    List all snippets, or create a new snippet.
    """

    def post(self, request, format=None):

        # Possibly relevant information about the person you talk to & their business that you can use:
        # [relevant scraped data]
        convo = []
        status_number = None
        statuscheck = None

        tracker = RequestTracker.objects.get(pk=1)

        request_count = tracker.request_count
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        print(request_count)
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

        if request_count == 1:
            status_prompt = f"""
                Categorize the following statuses and match the
                following dm within the triple backticks ```{request.data.get('text')}``` with the
                right status below from
                the following list of statuses
                0. sounds like anything outside the topics mentioned below or sounds like
                acknowledgement of a compliment
                1. sounds like an answer to 'What is the most frustrating part of your
                barber gig?' or indication of a
                problem not mentioned in the other points
                2. sounds like an answer to 'What is more important between managing
                current clients and attracting new
                ones?'
                3. sounds like an answer to 'How do you manage your calendar?' or
                'What is your [barber] booking system?'
                Do not match it to more than one status just simply give me something
                sensible based on the statuses that
                I have given you!
                Return the status number in double backticks!
                Always return a status number!!
            """
            state = query_gpt(status_prompt)
            status_number = get_status_number(state.get("choices")[0].get("message").get("content"))

        if request_count > 1:
            statuschecks = StatusCheck.objects.filter(stage=status_number)
            if statuschecks.exists():
                statuscheck = statuschecks.last()

        print(statuscheck.stage)
        try:
            req = request.data
            # logging.warn('request data', req)
            query_result = req.get("fulfillmentInfo")
            print(query_result)
            query = req.get("text")
            if query_result.get("tag") == "fallback":
                print(query)
                convo.append("DM:" + query)
                if statuscheck.stage in range(0, 2):
                    convo.append(prompts.get(statuscheck.stage + 1))
                elif statuscheck.stage == 3:
                    pass

                prompt = ("\n").join(convo)
                # logging.warn('prompt so far', convo)
                response = query_gpt(prompt)

                # logging.warn('gpt resp', response)
                result = response.get("choices")[0].get("message").get("content")
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
