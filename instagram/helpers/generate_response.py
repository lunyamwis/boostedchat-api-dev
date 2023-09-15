from django.shortcuts import get_object_or_404
from django_celery_beat.models import PeriodicTask

from instagram.helpers.llm import query_gpt
from instagram.models import Account, StatusCheck, Thread
from instagram.tasks import follow_user


class GenerateResponse(object):
    def __init__(self, status: str, thread: Thread) -> None:
        self.status = status
        self.followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread.account.igname}")
        self.thread = thread

    def if_followup_task_delete(self):
        try:
            followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{self.thread.account.igname}")
            followup_task.delete()
        except Exception as error:
            print(error)

    def check_responded_to_first_compliment(self, thread, lead_text):
        self.if_followup_task_delete()

        enforced_shared_compliment = query_gpt(
            f"""
            respond the following dm within the triple backticks
            ```{lead_text}``` in a friendly tone
            """
        )

        generated_response = enforced_shared_compliment.get("choices")[0].get("text")

        follow_user.delay(thread.account.igname)
        statuscheck, _ = StatusCheck.objects.update_or_create(stage=2, name="preparing_to_send_first_question")

        account = Account.objects.get(id=thread.account.id)
        account.status = statuscheck
        account.save()

        return generated_response

    def check_sent_first_question(self, thread, lead_text):

        try:
            followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread.account.igname}")
            followup_task.delete()
        except Exception as error:
            print(error)

        rephrase_defined_problem = query_gpt(
            f"""
            rephrase the problem stated in the followin dm within the triple backticks
            ```{lead_text}``` in a friendly tone add emoji that indicate
            you are in sympathy with them
            """
        )
        generated_response = rephrase_defined_problem.get("choices")[0].get("text")
        print(generated_response)
        statuscheck, _ = StatusCheck.objects.update_or_create(stage=2, name="preparing_to_send_second_question")
        account = get_object_or_404(Account, id=thread.account.id)
        account.status = statuscheck
        account.save()
