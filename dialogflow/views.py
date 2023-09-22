import logging

from prompt import prompts
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from instagram.helpers.llm import query_gpt

from .helpers.get_status_number import get_status_number


class FallbackWebhook(APIView):
    """
    List all snippets, or create a new snippet.
    """

    def post(self, request, format=None):

        # Possibly relevant information about the person you talk to & their business that you can use:
        # [relevant scraped data]
        convo = []
        status_prompt = f"""
            Categorize the stage of the conversation meant to sell Booksy. Check the following statuses and match the resulting dm from the prospect within the triple backticks ```{request.data.get('text')}``` with the right status below from the
            following list of statuses
            1. sounds like an answer to 'What is the most frustrating part of your barber gig?' or indication of a problem not mentioned in the other points
            2. sounds like an answer to 'What is more important between managing current clients and attracting new ones?'
            3. sounds like an answer to 'How do you manage your calendar?' or 'What is your [barber] booking system?'
            4. sounds like a complaint to the extra fees charged on their barber booking system that is being used.
            5. sounds like an answer to 'How do you get new clients?'
            6. sounds like a complaint on illegitimate reviews they are receiving from their barber booking system.
            7. content has an @ sign within it
            8. sounds like they are interested in trying out booksy or are already using it
            9. sounds like they are not interested in trying out booksy
            10. sounds like a detailed question or objection about the booking system
            return the status number in double ticks
        """
        state = query_gpt(status_prompt)
        status_number = get_status_number(state.get("choices")[0].get("message").get("content"))

        try:
            req = request.data
            # logging.warn('request data', req)
            query_result = req.get("fulfillmentInfo")
            print(query_result)
            query = req.get("text")
            # import pdb;pdb.set_trace()
            if query_result.get("tag") == "fallback":
                print(query)
                convo.append(query)
                convo.append(prompts.get(status_number + 1))
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
