import json
import logging
import uuid
from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from data.helpers.random_data import get_random_compliment
from instagram.models import Account, StatusCheck, Thread

from .llm import query_gpt


class CheckResponse(object):
    def __init__(self, status: str, thread: Thread) -> None:
        self.status = status
        self.daily_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="*/30",
            hour="*",
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
        )
        self.monthly_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="*/40",
            hour="*",
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
        )
        self.instance = thread

    def follow_up_task(self, message):
        task = None
        try:
            task, _ = PeriodicTask.objects.get_or_create(
                name=f"FollowupTask-{self.instance.account.igname}",
                crontab=self.daily_schedule,
                task="instagram.tasks.send_message",
                args=json.dumps([[message], [self.instance.thread_id]]),
                start_time=timezone.now(),
            )
        except Exception as error:
            task = PeriodicTask.objects.get(name=f"FollowupTask-{self.instance.account.igname}")
            task.args = json.dumps([[message], [self.instance.thread_id]])
            task.save()
            logging.warning(str(error))

        if timezone.now() >= task.start_time + timedelta(minutes=35):
            followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{self.instance.account.igname}")
            followup_task.crontab = self.monthly_schedule
            followup_task.save()

    def follow_up_if_responded_to_first_compliment(self, thread):
        pass

    def follow_up_if_sent_first_compliment(self):
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

        compliment = enforced_shared_compliment.get("choices")[0].get("message").get("content")

        self.follow_up_task(message=compliment)

    def follow_up_if_sent_first_question(self):
        salesrep = self.instance.account.salesrep_set.get(instagram=self.instance.account)
        compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
        self.follow_up_task(message=compliment)

    def follow_up_if_sent_second_question(self):
        salesrep = self.instance.account.salesrep_set.get(instagram=self.instance.account)
        random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
        self.folow_up_task(message=random_compliment)

    def follow_up_if_sent_third_question(self):
        salesrep = self.instance.account.salesrep_set.get(instagram=self.instance.account)
        random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
        self.folow_up_task(message=random_compliment)

    def follow_up_if_sent_first_needs_assessment_question(self):
        salesrep = self.instance.account.salesrep_set.get(instagram=self.instance.account)
        random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
        self.folow_up_task(message=random_compliment)

    def follow_up_if_sent_second_needs_assessment_question(self):
        salesrep = self.instance.account.salesrep_set.get(instagram=self.instance.account)
        random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
        self.folow_up_task(message=random_compliment)

    def follow_up_if_sent_third_needs_assessment_question(self):
        salesrep = self.instance.account.salesrep_set.get(instagram=self.instance.account)
        random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
        self.follow_up_task(message=random_compliment)

    def follow_up_after_solutions_presented(self):
        random_compliment = f""""
            What do you think about booksy?\n
            Would you like to give it a try?
            """
        self.follow_up_task(message=random_compliment)

    def follow_up_after_presentation(self):
        if self.instance.account.dormant_profile_created:
            booksy_status, _ = StatusCheck.objects.get_or_create(stage=2, name="Trial")

            account = get_object_or_404(Account, id=self.instance.account.id)
            account.status = booksy_status
            account.save()

            random_compliment = f""""
                What's up {self.instance.account.igname} let us make the most of your free trial account?
                you can manage it all with https://dl.booksy.com/WSlwk9kUhCb
                (login: {self.instance.account.igname} password: {str(uuid.uuid4())}) to
                [solution to combination of problems]
                DM: let me know what you think and I’ll guide you for a month to grow it like crazy:)
                """
            self.follow_up_task(message=random_compliment)

    def follow_up_if_sent_email_first_attempt(self):
        combination_of_problems = []
        random_compliment = f"""
            I actually think Booksy will help you big time {combination_of_problems}
            Let me know your email address and I’ll help you with the setup;)
            """
        task = None
        try:
            task, _ = PeriodicTask.objects.get_or_create(
                name=f"FollowupTask-{self.instance.account.igname}",
                crontab=self.daily_schedule,
                task="instagram.tasks.send_message",
                args=json.dumps([[random_compliment], [self.instance.thread_id]]),
                start_time=timezone.now(),
            )
        except Exception as error:
            task = PeriodicTask.objects.get(name=f"FollowupTask-{self.instance.account.igname}")
            task.args = json.dumps([[random_compliment], [self.instance.thread_id]])
            task.save()
            logging.warning(str(error))

        if timezone.now() >= task.start_time + timedelta(minutes=4):
            second_attempt = """
                When you see your profile on Booksy you won’t believe that you
                used to [combination of problems].
                What’s your valid email address?
                """
            followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{self.instance.account.igname}")
            followup_task.crontab = self.monthly_schedule
            task.args = json.dumps([[second_attempt], [self.instance.thread_id]])
            followup_task.save()

            status_after_response, _ = StatusCheck.objects.get_or_create(stage=2, name="sent_email_second_attempt")
            account = get_object_or_404(Account, id=self.instance.account.id)
            account.status = status_after_response
            account.save()

        if timezone.now() >= task.start_time + timedelta(minutes=3):
            third_attempt = """
                I can see you’re pretty busy and wanted to create profile on Booksy for you to
                elevate your business,
                I’ll just need your email address:)
                """
            followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{self.instance.account.igname}")
            followup_task.crontab = self.monthly_schedule
            task.args = json.dumps([[third_attempt], [self.instance.thread_id]])
            followup_task.save()

            status_after_response, _ = StatusCheck.objects.get_or_create(stage=3, name="sent_email_last_attempt")
            account = get_object_or_404(Account, id=self.instance.account.id)
            account.status = status_after_response
            account.save()

    def follow_up_if_sent_uninterest(self, thread_):
        rephrase_defined_problem = query_gpt(
            """
                ask for the more detailed reason why they are not interested
                """
        )
        random_compliment = rephrase_defined_problem.get("choices")[0].get("message").get("content")
        self.follow_up_task(message=random_compliment)

    def follow_up_if_sent_objection(self, thread_):
        salesrep = thread_.account.salesrep_set.get(instagram=thread_.account)
        random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
        self.follow_up_task(message=random_compliment)
