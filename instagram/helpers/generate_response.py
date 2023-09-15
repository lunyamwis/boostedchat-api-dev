from instagram.helpers.llm import query_gpt
from instagram.tasks import follow_user
from instagram.models import Account, StatusCheck
from django_celery_beat.models import PeriodicTask


class GenerateResponse(object):
    def __init__(self, status: str, thread) -> None:
        self.status = status
        self.followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread.account.igname}")

    def check_responded_to_first_compliment(self, thread, lead_text):
        try:
            followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread.account.igname}")
            followup_task.delete()
        except Exception as error:
            print(error)

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

    def check_sent_first_question(self, thread):

        try:
            followup_task = PeriodicTask.objects.get(name=f"FollowupTask-{thread.account.igname}")
            followup_task.delete()
        except Exception as error:
            print(error)

        rephrase_defined_problem = query_gpt(
            f"""
            rephrase the problem stated in the followin dm within the triple backticks
            ```{request.data.get("text")}``` in a friendly tone add emoji that indicate
            you are in sympathy with them
            """
        )
        generated_response = rephrase_defined_problem.get("choices")[0].get("text")
        statuscheck, _ = StatusCheck.objects.update_or_create(stage=2, name="preparing_to_send_second_question")
        account = get_object_or_404(Account, id=thread.account.id)
        account.status = statuscheck
        account.save()
