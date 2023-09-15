import json
import logging
from datetime import timedelta

from django.utils import timezone
from django_celery_beat.models import CrontabSchedule, PeriodicTask

from data.helpers.random_data import get_random_compliment


class CheckResponse(object):
    def __init__(self, status: str) -> None:
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

    def follow_up_if_responded_to_first_compliment(self, thread):
        pass

    def follow_up_if_sent_first_compliment(self, thread_):
        salesrep = thread_.account.salesrep_set.get(instagram=thread_.account)
        random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
        task = None
        try:
            task, _ = PeriodicTask.objects.get_or_create(
                name=f"FollowupTask-{thread_.account.igname}",
                crontab=self.daily_schedule,
                task="instagram.tasks.send_message",
                args=json.dumps([[random_compliment], [thread_.thread_id]]),
                start_time=timezone.now(),
            )
        except Exception as error:
            task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
            task.args = json.dumps([[random_compliment], [thread_.thread_id]])
            task.save()
            logging.warning(str(error))

        if timezone.now() >= task.start_time + timedelta(minutes=4):
            followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
            followup_task.crontab = self.monthly_schedule
            followup_task.save()

    def follow_up_if_sent_second_question(self, thread_):

        salesrep = thread_.account.salesrep_set.get(instagram=thread_.account)
        random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
        task = None
        try:
            task, _ = PeriodicTask.objects.get_or_create(
                name=f"FollowupTask-{thread_.account.igname}",
                crontab=self.daily_schedule,
                task="instagram.tasks.send_message",
                args=json.dumps([[random_compliment], [thread_.thread_id]]),
                start_time=timezone.now(),
            )
        except Exception as error:
            task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
            task.args = json.dumps([[random_compliment], [thread_.thread_id]])
            task.save()
            logging.warning(str(error))

        if timezone.now() >= task.start_time + timedelta(minutes=4):
            followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
            followup_task.crontab = self.monthly_schedule
            followup_task.save()

    def follow_up_if_sent_third_question(self, thread_):
        salesrep = thread_.account.salesrep_set.get(instagram=thread_.account)
        random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
        task = None
        try:
            task, _ = PeriodicTask.objects.get_or_create(
                name=f"FollowupTask-{thread_.account.igname}",
                crontab=self.daily_schedule,
                task="instagram.tasks.send_message",
                args=json.dumps([[random_compliment], [thread_.thread_id]]),
                start_time=timezone.now(),
            )
        except Exception as error:
            task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
            task.args = json.dumps([[random_compliment], [thread_.thread_id]])
            task.save()
            logging.warning(str(error))

        if timezone.now() >= task.start_time + timedelta(minutes=4):
            followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
            followup_task.crontab = self.monthly_schedule
            followup_task.save()

    def follow_up_if_sent_first_needs_assessment_question(self, thread_):
        salesrep = thread_.account.salesrep_set.get(instagram=thread_.account)
        random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
        task = None
        try:
            task, _ = PeriodicTask.objects.get_or_create(
                name=f"FollowupTask-{thread_.account.igname}",
                crontab=self.daily_schedule,
                task="instagram.tasks.send_message",
                args=json.dumps([[random_compliment], [thread_.thread_id]]),
                start_time=timezone.now(),
            )
        except Exception as error:
            task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
            task.args = json.dumps([[random_compliment], [thread_.thread_id]])
            task.save()
            logging.warning(str(error))

        if timezone.now() >= task.start_time + timedelta(minutes=4):
            followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
            followup_task.crontab = self.monthly_schedule
            followup_task.save()

    def follow_up_if_sent_second_needs_assessment_question(self, thread_):
        salesrep = thread_.account.salesrep_set.get(instagram=thread_.account)
        random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
        task = None
        try:
            task, _ = PeriodicTask.objects.get_or_create(
                name=f"FollowupTask-{thread_.account.igname}",
                crontab=self.daily_schedule,
                task="instagram.tasks.send_message",
                args=json.dumps([[random_compliment], [thread_.thread_id]]),
                start_time=timezone.now(),
            )
        except Exception as error:
            task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
            task.args = json.dumps([[random_compliment], [thread_.thread_id]])
            task.save()
            logging.warning(str(error))

        if timezone.now() >= task.start_time + timedelta(minutes=4):
            followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
            followup_task.crontab = self.monthly_schedule
            followup_task.save()

    def follow_up_if_sent_third_needs_assessment_question(self, thread_):
        salesrep = thread_.account.salesrep_set.get(instagram=thread_.account)
        random_compliment = get_random_compliment(salesrep=salesrep, compliment_type="first_compliment")
        task = None
        try:
            task, _ = PeriodicTask.objects.get_or_create(
                name=f"FollowupTask-{thread_.account.igname}",
                crontab=self.daily_schedule,
                task="instagram.tasks.send_message",
                args=json.dumps([[random_compliment], [thread_.thread_id]]),
                start_time=timezone.now(),
            )
        except Exception as error:
            task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
            task.args = json.dumps([[random_compliment], [thread_.thread_id]])
            task.save()
            logging.warning(str(error))

        if timezone.now() >= task.start_time + timedelta(minutes=4):
            followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread_.account.igname}")
            followup_task.crontab = self.monthly_schedule
            followup_task.save()
