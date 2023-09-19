import json
import logging
from datetime import timedelta

from django.utils import timezone
from django_celery_beat.models import CrontabSchedule, PeriodicTask
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from instagram.helpers.llm import query_gpt


class FallbackWebhook(APIView):
    """
    List all snippets, or create a new snippet.
    """

    def post(self, request, format=None):
        prompts = {
            "NA": f"""
        Act as if you were an Instagram DM-based sales representative for the biggest
        beauty appointment management system & marketplace called Booksy. Respond to the received
        DM from a US-based [category] in a way that builds a relationship (make any small talk personal
        but brief as we need to focus on the conversation goal stated below) and helps us achieve the current
        conversation goal. Each message needs to be a short DM message in a way that sounds natural and engaging,
        confirming that we believe that the [category] is a great professional and we understand their point of
        view. make sure to use a tone of voice in line with those characteristics: "We’re revolutionizing the way
        people make appointments. Barbers and stylists are frustrated from wasting too much time managing their
        books when they could be focusing on their craft. Booksy offers a platform for them to streamline
        business management. Both a reliable receptionist and a trustworthy business partner,
        Booksy helps merchants grow and gives them time to master their skills.
        CONVERSATIONAL We are a business partner and friendly neighbor recommending a service or business.
        Our voice needs to match our attitude. Being corporate is too rigid, and can be alienating.
        Speaking casually and candidly allows customers to trust us. ENCOURAGING Our customers and
        merchants dream of fulfilling their full personal potential, and Booksy gives them the tools
        to accomplish that. GENUINE Booksy makes a promise to its customers. We’re adding a new meaning
        to their lives by redefining what it means to manage a business. How? By being accurate, honest,
        transparent, and receptive to customer feedback."
        Interaction so far: [{request.data.get("text")}]
        At this point, you want to steer the friendly conversation to not go past five minutes
        Don't use more than 3 sentences and 15-20 words.
        """
        }
        # Possibly relevant information about the person you talk to & their business that you can use:
        # [relevant scraped data]
        convo = []
        schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="*/5",
            hour="*",
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
        )
        try:
            req = request.data
            # logging.warn('request data', req)
            query_result = req.get("fulfillmentInfo")
            print(query_result)
            query = req.get("text")
            # import pdb;pdb.set_trace()
            if query_result.get("tag") == "fallback":
                print(query)
                convo.append("DM:" + query)
                convo.append(prompts.get("NA"))
                prompt = ("\n").join(convo)
                # logging.warn('prompt so far', convo)
                response = query_gpt(prompt)

                # logging.warn('gpt resp', response)
                result = response.get("choices")[0].get("message").get("content")
                result = result.strip("\n")
                logging.warn(result)
                convo.append(result)
                logging.warn(str(["convo so far", ("\n").join(convo)]))
                # unique_id = str(uuid.uuid4())
                first_question = "By the way, What is the gnarliest part of your barber gig?"
                task = None
                try:
                    task, _ = PeriodicTask.objects.get_or_create(
                        name=f"FollowupTask-{1}",
                        crontab=schedule,
                        task="instagram.tasks.send_message",
                        args=json.dumps([[first_question], ["340282366841710301244276030187054119912"]]),
                        start_time=timezone.now(),
                    )
                except Exception as error:
                    print(error)
                    task = PeriodicTask.objects.get(name=f"FollowupTask-{1}")

                if timezone.now() >= task.start_time + timedelta(minutes=5):
                    return Response(
                        {
                            "fulfillment_response": {
                                "messages": [
                                    {
                                        "text": {
                                            "text": [first_question],
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
