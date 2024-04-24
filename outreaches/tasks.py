from celery import shared_task

@shared_task()
def daily_reshedule_outreach():
    # Task logic here
    result = 1 + 2
    return result
