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
            minute="*/4",
            hour="*",
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
        )
        self.monthly_schedule, _ = CrontabSchedule.objects.get_or_create(
            minute="*/6",
            hour="*",
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
        )
        self.thread = thread

    def follow_up_task(self, message):
        task = None
        try:
            task, _ = PeriodicTask.objects.get_or_create(
                name=f"FollowupTask-{self.thread.account.igname}",
                crontab=self.daily_schedule,
                task="instagram.tasks.send_message",
                args=json.dumps([[message], [self.thread.thread_id]]),
                start_time=timezone.now(),
            )
        except Exception as error:
            task = PeriodicTask.objects.get(name=f"FollowupTask-{self.thread.account.igname}")
            task.args = json.dumps([[message], [self.thread.thread_id]])
            task.save()
            logging.warning(str(error))

        if timezone.now() >= task.start_time + timedelta(minutes=4):
            followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{self.thread.account.igname}")
            followup_task.crontab = self.monthly_schedule
            followup_task.save()

    def follow_up_if_responded_to_first_compliment(self, thread):
        pass

    def follow_up_if_sent_first_compliment(self):
        salesrep = self.thread.account.salesrep_set.get(instagram=self.thread.account)
        compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
        self.follow_up_task(message=compliment)

    def follow_up_if_sent_second_question(self):
        salesrep = self.thread.account.salesrep_set.get(instagram=self.thread.account)
        random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
        self.folow_up_task(message=random_compliment)

    def follow_up_if_sent_third_question(self):
        salesrep = self.thread.account.salesrep_set.get(instagram=self.thread.account)
        random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
        self.folow_up_task(message=random_compliment)

    def follow_up_if_sent_first_needs_assessment_question(self):
        salesrep = self.thread.account.salesrep_set.get(instagram=self.thread.account)
        random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
        self.folow_up_task(message=random_compliment)

    def follow_up_if_sent_second_needs_assessment_question(self):
        salesrep = self.thread.account.salesrep_set.get(instagram=self.thread.account)
        random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
        self.folow_up_task(message=random_compliment)

    def follow_up_if_sent_third_needs_assessment_question(self):
        salesrep = self.thread.account.salesrep_set.get(instagram=self.thread.account)
        random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
        self.folow_up_task(message=random_compliment)

    def follow_up_if_sent_follow_up_after_presentation(self):
        if self.thread.account.dormant_profile_created:
            booksy_status, _ = StatusCheck.objects.get_or_create(stage=2, name="Trial")

            account = get_object_or_404(Account, id=self.thread.account.id)
            account.status = booksy_status
            account.save()

            random_compliment = f""""
                What's up {self.thread.account.igname} let us make the most of your free trial account?
                you can manage it all with https://dl.booksy.com/WSlwk9kUhCb
                (login: {self.thread.account.igname} password: {str(uuid.uuid4())}) to
                [solution to combination of problems]
                DM: let me know what you think and I’ll guide you for a month to grow it like crazy:)
                """
            self.folow_up_task(message=random_compliment)

    def follow_up_if_sent_email_first_attempt(self):
        combination_of_problems = []
        random_compliment = f"""
            I actually think Booksy will help you big time {combination_of_problems}
            Let me know your email address and I’ll help you with the setup;)
            """
        task = None
        try:
            task, _ = PeriodicTask.objects.get_or_create(
                name=f"FollowupTask-{self.thread.account.igname}",
                crontab=self.daily_schedule,
                task="instagram.tasks.send_message",
                args=json.dumps([[random_compliment], [self.thread.thread_id]]),
                start_time=timezone.now(),
            )
        except Exception as error:
            task = PeriodicTask.objects.get(name=f"FollowupTask-{self.thread.account.igname}")
            task.args = json.dumps([[random_compliment], [self.thread.thread_id]])
            task.save()
            logging.warning(str(error))

        if timezone.now() >= task.start_time + timedelta(minutes=4):
            second_attempt = """
                When you see your profile on Booksy you won’t believe that you
                used to [combination of problems].
                What’s your valid email address?
                """
            followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{self.thread.account.igname}")
            followup_task.crontab = self.monthly_schedule
            task.args = json.dumps([[second_attempt], [self.thread.thread_id]])
            followup_task.save()

            status_after_response, _ = StatusCheck.objects.get_or_create(stage=2, name="sent_email_second_attempt")
            account = get_object_or_404(Account, id=self.thread.account.id)
            account.status = status_after_response
            account.save()

        if timezone.now() >= task.start_time + timedelta(minutes=3):
            third_attempt = """
                I can see you’re pretty busy and wanted to create profile on Booksy for you to
                elevate your business,
                I’ll just need your email address:)
                """
            followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{self.thread.account.igname}")
            followup_task.crontab = self.monthly_schedule
            task.args = json.dumps([[third_attempt], [self.thread.thread_id]])
            followup_task.save()

            status_after_response, _ = StatusCheck.objects.get_or_create(stage=3, name="sent_email_last_attempt")
            account = get_object_or_404(Account, id=self.thread.account.id)
            account.status = status_after_response
            account.save()

    def follow_up_if_sent_uninterest(self, thread_):
        rephrase_defined_problem = query_gpt(
            """
                ask for the more detailed reason why they are not interested
                """
        )
        random_compliment = rephrase_defined_problem.get("choices")[0].get("text")
        self.follow_up_task(message=random_compliment)

    def follow_up_if_sent_objection(self, thread_):
        salesrep = thread_.account.salesrep_set.get(instagram=thread_.account)
        random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
        self.follow_up_task(message=random_compliment)
