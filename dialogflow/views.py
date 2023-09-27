import logging
import re

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from instagram.helpers.check_response import CheckResponse
from instagram.helpers.llm import query_gpt
from instagram.models import StatusCheck, Thread

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

        after_response = CheckResponse(status="confirmed_problem", thread=thread)
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
                    if statuscheck.name != "sent_first_question":
                        convo.append(get_prompt(statuscheck.stage - 1, client_message=query))
                    if statuscheck.name == "sent_first_question":
                        convo.append(get_prompt(statuscheck.stage - 1, client_message=query))
                    if statuscheck.name == "confirmed_problem":
                        convo.append(get_prompt(statuscheck.stage - 1, client_message=query))
                elif statuscheck.stage == 3:
                    pass

                prompt = ("\n").join(convo)
                response = query_gpt(prompt)

                result = response.get("choices")[0].get("message").get("content")

                result = result.strip("\n")
                confirmed_rejected_problems_arr = re.findall(r"\+\+(.*?)\+\+", result)
                confirmation_counter = 0
                for problem in confirmed_rejected_problems_arr:
                    if "confirmed" in problem:
                        confirmation_counter += 1

                if confirmation_counter > 2:
                    statuscheck.name = "confirmed_problem"
                    statuscheck.save()
                    after_response.follow_up_after_solutions_presented()
                    after_response.follow_up_if_sent_email_first_attempt()

                if statuscheck.name == "sent_first_question":
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
                    thread.content = f"barber:{query},you:{result}"
                    thread.save()
                else:
                    pass

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
