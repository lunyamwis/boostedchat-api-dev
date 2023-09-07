from celery import shared_task

from instagram.helpers.login import login_user
from instagram.models import Account, Thread


@shared_task()
def send_comment(media_link, generated_response):
    cl = login_user()
    media_pk = cl.media_pk_from_url(media_link)
    media_id = cl.media_id(media_pk=media_pk)
    cl = login_user()
    cl.media_comment(media_id, generated_response)


@shared_task()
def send_message(message, thread_id=None, user_id=None, username=None, thread=True):
    cl = login_user()
    user_id = None
    if username:
        user_id = cl.user_id_from_username(username)
        try:
            account = Account.objects.get(igname=username)
        except Exception as error:
            print(error)
        message = cl.direct_send(message, user_ids=[user_id])
        thread = Thread()
        thread.thread_id = message.thread_id
        thread.account = account
        thread.save()
    if thread_id and thread:
        cl.direct_send(message, thread_ids=[thread_id])
