from datetime import date, timedelta

from django.shortcuts import get_object_or_404
from django_celery_beat.models import PeriodicTask

from instagram.helpers.llm import query_gpt
from instagram.models import Account, StatusCheck, Thread
from instagram.tasks import follow_user


class GenerateResponse(object):
    def __init__(self, status: str, thread: Thread, lead_response: str) -> None:
        self.status = status
        self.instance = thread
        self.lead_response = lead_response

    def if_followup_task_delete(self):
        try:
            followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{self.instance.account.igname}")
            followup_task.delete()
        except Exception as error:
            print(error)

    def update_account_status(self, stage, new_status):
        statuscheck, _ = StatusCheck.objects.update_or_create(stage=stage, name=new_status)

        account = get_object_or_404(Account, id=self.instance.account.id)
        account.status = statuscheck
        account.save()

    def check_responded_to_first_compliment(self):
        self.if_followup_task_delete()

        prompt = """
            mention in your instagram-like message that you're sure that they remember their positive reviews but you think that reviews like the one from [get reviewer name from the reviewerNameAndDate from the list of reviews in the data within the triple backticks] that [get reviewer text from the review_text from the list of reviews in the data within the triple backticks and rephrase the review] result in plenty of referrals from their clients.
            here is an example that can guide you;
            example:  I had my browser still open on your profile and Iove what your clients are saying [get reviewServiceName in the reviews list within the data in the triple backticks and then summarize what they said in the review_text in the reviews list within the data in the triple backticks]
            complete this example with an encouraging remark that will keep them moving on.
            ```[
            {
                "name": "styleseat",
                "secondary_name": "Paul",
                "category": "Barber",
                "businessName": "Business name: The Fine Grooming Studio",
                "ratings": "5.0\n(535)",
                "reviews": [
                {
                    "reviews": "5.0 (535 Reviews)\n1\n<1%\n2\n<1%\n3\n<1%\n4\n3%\n5\n96%",
                    "clientPhotosNo": "Get $50",
                    "review_text": "”It was great to meet Paul, who gonna be my new barber, beard stylist. This guy and the whole place seemed chill and relaxing. Great service and attention to detail. Solid place to go to. I’ll be back, no doubt.“",
                    "aboutClientAdjectives": "ATTENTIVE\nON TIME\nPROFESSIONAL",
                    "aboutClientLocation": "CLEAN\nEASY PARKING",
                    "reviewerNameAndDate": "JEFF T.\nFeb 25, 2023",
                    "reviewServiceName": "Beard Line-up | Sculpting"
                },
                {
                    "reviews": "5.0 (535 Reviews)\n1\n<1%\n2\n<1%\n3\n<1%\n4\n3%\n5\n96%",
                    "clientPhotosNo": "Get $50",
                    "review_text": "”It was great to meet Paul, who gonna be my new barber, beard stylist. This guy and the whole place seemed chill and relaxing. Great service and attention to detail. Solid place to go to. I’ll be back, no doubt.“",
                    "aboutClientAdjectives": "ATTENTIVE\nON TIME\nPROFESSIONAL",
                    "aboutClientLocation": "CLEAN\nEASY PARKING",
                    "reviewerNameAndDate": "JEFF T.\nFeb 25, 2023",
                    "reviewServiceName": "Beard Line-up | Sculpting"
                },
                {
                    "reviews": "5.0 (535 Reviews)\n1\n<1%\n2\n<1%\n3\n<1%\n4\n3%\n5\n96%",
                    "clientPhotosNo": "Get $50",
                    "review_text": "”It was great to meet Paul, who gonna be my new barber, beard stylist. This guy and the whole place seemed chill and relaxing. Great service and attention to detail. Solid place to go to. I’ll be back, no doubt.“",
                    "aboutClientAdjectives": "ATTENTIVE\nON TIME\nPROFESSIONAL",
                    "aboutClientLocation": "CLEAN\nEASY PARKING",
                    "reviewerNameAndDate": "JEFF T.\nFeb 25, 2023",
                    "reviewServiceName": "Beard Line-up | Sculpting"
                },
                {
                    "reviews": "5.0 (535 Reviews)\n1\n<1%\n2\n<1%\n3\n<1%\n4\n3%\n5\n96%",
                    "clientPhotosNo": "Get $50",
                    "review_text": "”It was great to meet Paul, who gonna be my new barber, beard stylist. This guy and the whole place seemed chill and relaxing. Great service and attention to detail. Solid place to go to. I’ll be back, no doubt.“",
                    "aboutClientAdjectives": "ATTENTIVE\nON TIME\nPROFESSIONAL",
                    "aboutClientLocation": "CLEAN\nEASY PARKING",
                    "reviewerNameAndDate": "JEFF T.\nFeb 25, 2023",
                    "reviewServiceName": "Beard Line-up | Sculpting"
                },
                {
                    "reviews": "5.0 (535 Reviews)\n1\n<1%\n2\n<1%\n3\n<1%\n4\n3%\n5\n96%",
                    "clientPhotosNo": "Get $50",
                    "review_text": "”It was great to meet Paul, who gonna be my new barber, beard stylist. This guy and the whole place seemed chill and relaxing. Great service and attention to detail. Solid place to go to. I’ll be back, no doubt.“",
                    "aboutClientAdjectives": "ATTENTIVE\nON TIME\nPROFESSIONAL",
                    "aboutClientLocation": "CLEAN\nEASY PARKING",
                    "reviewerNameAndDate": "JEFF T.\nFeb 25, 2023",
                    "reviewServiceName": "Beard Line-up | Sculpting"
                },
                {
                    "reviews": "5.0 (535 Reviews)\n1\n<1%\n2\n<1%\n3\n<1%\n4\n3%\n5\n96%",
                    "clientPhotosNo": "Get $50",
                    "review_text": "”It was great to meet Paul, who gonna be my new barber, beard stylist. This guy and the whole place seemed chill and relaxing. Great service and attention to detail. Solid place to go to. I’ll be back, no doubt.“",
                    "aboutClientAdjectives": "ATTENTIVE\nON TIME\nPROFESSIONAL",
                    "aboutClientLocation": "CLEAN\nEASY PARKING",
                    "reviewerNameAndDate": "JEFF T.\nFeb 25, 2023",
                    "reviewServiceName": "Beard Line-up | Sculpting"
                },
                {
                    "reviews": "5.0 (535 Reviews)\n1\n<1%\n2\n<1%\n3\n<1%\n4\n3%\n5\n96%",
                    "clientPhotosNo": "Get $50",
                    "review_text": "”It was great to meet Paul, who gonna be my new barber, beard stylist. This guy and the whole place seemed chill and relaxing. Great service and attention to detail. Solid place to go to. I’ll be back, no doubt.“",
                    "aboutClientAdjectives": "ATTENTIVE\nON TIME\nPROFESSIONAL",
                    "aboutClientLocation": "CLEAN\nEASY PARKING",
                    "reviewerNameAndDate": "JEFF T.\nFeb 25, 2023",
                    "reviewServiceName": "Beard Line-up | Sculpting"
                },
                {
                    "reviews": "5.0 (535 Reviews)\n1\n<1%\n2\n<1%\n3\n<1%\n4\n3%\n5\n96%",
                    "clientPhotosNo": "Get $50",
                    "review_text": "”It was great to meet Paul, who gonna be my new barber, beard stylist. This guy and the whole place seemed chill and relaxing. Great service and attention to detail. Solid place to go to. I’ll be back, no doubt.“",
                    "aboutClientAdjectives": "ATTENTIVE\nON TIME\nPROFESSIONAL",
                    "aboutClientLocation": "CLEAN\nEASY PARKING",
                    "reviewerNameAndDate": "JEFF T.\nFeb 25, 2023",
                    "reviewServiceName": "Beard Line-up | Sculpting"
                },
                {
                    "reviews": "5.0 (535 Reviews)\n1\n<1%\n2\n<1%\n3\n<1%\n4\n3%\n5\n96%",
                    "clientPhotosNo": "Get $50",
                    "review_text": "”It was great to meet Paul, who gonna be my new barber, beard stylist. This guy and the whole place seemed chill and relaxing. Great service and attention to detail. Solid place to go to. I’ll be back, no doubt.“",
                    "aboutClientAdjectives": "ATTENTIVE\nON TIME\nPROFESSIONAL",
                    "aboutClientLocation": "CLEAN\nEASY PARKING",
                    "reviewerNameAndDate": "JEFF T.\nFeb 25, 2023",
                    "reviewServiceName": "Beard Line-up | Sculpting"
                },

                ],
                "aboutName": [
                "Hi there, ",
                "Im Paul"
                ],
            }
            ]```
            Do not sound formal, be casual and friendly.
            Do not send greetings.
            Do not sign off.
            """
        enforced_shared_compliment = query_gpt(prompt=prompt)

        generated_response = enforced_shared_compliment.get("choices")[0].get("message").get("content")

        follow_user.delay(self.instance.account.igname)

        self.update_account_status(2, "preparing_to_send_first_question")

        return generated_response

    def check_sent_first_question(self):

        self.if_followup_task_delete()

        rephrase_defined_problem = query_gpt(
            f"""
            rephrase the problem stated in the followin dm within the triple backticks
            ```{self.lead_response}``` in a friendly tone add emoji that indicate
            you are in sympathy with them
            """
        )
        generated_response = rephrase_defined_problem.get("choices")[0].get("message").get("content")

        self.update_account_status(2, "preparing_to_send_second_question")

        return generated_response

    def check_sent_second_question(self):
        last_seven_days = [date.today() - timedelta(days=day) for day in range(7)]
        if self.instance.account.outsourced:
            if self.instance.account.outsourced.updated_at.date() in last_seven_days:
                pass
        else:
            self.if_followup_task_delete()

            rephrase_defined_problem = query_gpt(
                f"""
                rephrase the importance stated in the following dm within the triple backticks
                ```{self.lead_response}``` in a friendly tone add emoji that indicate
                you are affirming what they are saying
                """
            )
            generated_response = rephrase_defined_problem.get("choices")[0].get("message").get("content")

            self.update_account_status(2, "preparing_to_send_third_question")

            return generated_response

    def check_sent_third_question(self):
        booking_system = None
        last_seven_days = [date.today() - timedelta(days=day) for day in range(7)]
        if booking_system and self.instance.account.outsourced.updated_at.date() in last_seven_days:
            pass
        else:
            self.if_followup_task_delete()

            rephrase_defined_problem = query_gpt(
                f"""
                respond to the following dm within the triple backticks
                ```{self.lead_response}``` in a way that shows that you have understood them.
                """
            )
            generated_response = rephrase_defined_problem.get("choices")[0].get("message").get("content")

            self.update_account_status(2, "preparing_to_send_first_needs_assessment_question")

            return generated_response

    def check_sent_first_needs_assessment_question(self):
        confirm_reject_problem = True
        if confirm_reject_problem:
            self.if_followup_task_delete()

            rephrase_defined_problem = query_gpt(
                f"""
                respond to the following dm within the triple backticks
                ```{self.lead_response}``` in a way that shows that you have understood them.
                """
            )
            generated_response = rephrase_defined_problem.get("choices")[0].get("message").get("content")
            self.update_account_status(2, "preparing_to_send_second_needs_assessment_question")
            return generated_response
        else:
            pass

    def check_sent_second_needs_assessment_question(self):

        confirm_reject_problem = True
        if confirm_reject_problem:

            self.if_followup_task_delete()

            rephrase_defined_problem = query_gpt(
                f"""
                respond to the following dm within the triple backticks
                ```{self.lead_response}``` in a way that shows that you have understood them.
                """
            )
            generated_response = rephrase_defined_problem.get("choices")[0].get("message").get("content")
            self.update_account_status(2, "preparing_to_send_third_needs_assessment_question")
            return generated_response
        else:
            pass

    def check_sent_third_needs_assessment_question(self):

        confirm_reject_problem = True
        if confirm_reject_problem:

            self.if_followup_task_delete()

            rephrase_defined_problem = query_gpt(
                f"""
                respond to the following dm within the triple backticks
                ```{self.lead_response}``` in a way that shows that you have understood them.
                """
            )
            generated_response = rephrase_defined_problem.get("choices")[0].get("message").get("content")
            self.update_account_status(2, "follow_up_after_presentation")
            return generated_response
        else:
            pass

    def check_sent_follow_up_presententation(self):
        check_email = True

        generated_response = None

        if check_email:
            self.if_followup_task_delete()

            rephrase_defined_problem = query_gpt(
                f"""
                respond to the following dm within the triple backticks
                ```{self.lead_response}``` in a way that shows that you have understood them.
                """
            )
            generated_response = rephrase_defined_problem.get("choices")[0].get("message").get("content")
            self.update_account_status(2, "ask_for_email_first_attempt")

        else:
            interested = query_gpt(
                f"""
                analyse to the following dm within the triple backticks
                ```{self.lead_response}``` to know whether they are interested in the
                product or not and return
                a boolean of 0 -if not interested, and 1 -if interested and 2 -if have any objections.
                """
            )
            if int(interested) == 1:
                pass

            elif int(interested) == 0:
                rephrase_defined_problem = query_gpt(
                    f"""
                    rephrase the following dm within the triple backticks
                    ```{self.lead_response}``` asking them why they are not interested.
                    """
                )
                generated_response = rephrase_defined_problem.get("choices")[0].get("message").get("content")
                self.update_account_status(3, "ask_uninterest")
            elif int(interested) == 2:
                rephrase_defined_problem = query_gpt(
                    f"""
                    rephrase objection within the triple backticks
                    ```{self.lead_response}``` in a way
                    to show that they’re understood
                    """
                )
                generated_response = rephrase_defined_problem.get("choices")[0].get("message").get("content")
                self.update_account_status(3, "ask_objection")

        return generated_response
