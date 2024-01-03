from auditlog.models import AuditlogHistoryField
from auditlog.registry import auditlog
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from base.models import BaseModel

# Create your models here.


class OutSourcedInfo(models.Model):
    source = models.CharField(null=True, blank=True, max_length=255)
    results = models.TextField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)


class StatusCheck(BaseModel):
    STAGES = ((1, "Oven"), (2, "Needs Assessment"), (3, "Overcoming Objections"), (4, "Activation"))
    stage = models.IntegerField(choices=STAGES, default=1)
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return f"{self.stage} - {self.name}"

    def get_id(self):
        return self.id


class Account(BaseModel):
    igname = models.CharField(max_length=255, null=True, unique=False, blank=True)
    assigned_to = models.TextField(default="Robot")
    full_name = models.CharField(max_length=1024, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone_number = models.CharField(max_length=255, null=True, blank=True)
    profile_url = models.URLField(null=True, blank=True)
    status = models.ForeignKey(StatusCheck, on_delete=models.CASCADE, null=True, blank=True)
    confirmed_problems = models.TextField(null=True, blank=True, default="test")
    rejected_problems = models.TextField(null=True, blank=True, default="test")
    history = AuditlogHistoryField(pk_indexable=False)
    dormant_profile_created = models.BooleanField(default=True, null=True, blank=True)
    qualified = models.BooleanField(default=False)
    index = models.IntegerField(default=1)

    def __str__(self) -> str:
        return self.igname


class OutSourced(BaseModel):
    source = models.CharField(null=True, blank=True, max_length=255)
    results = models.JSONField()
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)


auditlog.register(Account)


class HashTag(BaseModel):
    hashtag_id = models.CharField(max_length=255)
    name = models.CharField(max_length=255, null=True, blank=True)


class Story(BaseModel):
    story_id = models.CharField(max_length=50, null=True, blank=True)
    link = models.URLField()


class Photo(BaseModel):
    photo_id = models.CharField(max_length=50)
    link = models.URLField()
    name = models.CharField(max_length=255)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)


class Thread(BaseModel):
    thread_id = models.CharField(max_length=255)
    account = models.ForeignKey(Account, on_delete=models.CASCADE, null=True, blank=True)
    unread_message_count = models.IntegerField(default=0)
    last_message_content = models.TextField(null=True, blank=True)
    last_message_at = models.DateTimeField(null=True, blank=True)


class Message(BaseModel):
    content = models.TextField(null=True, blank=True, default="test")
    sent_by = models.CharField(max_length=255, null=True, blank=True)
    sent_on = models.DateTimeField()
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, null=True, blank=True)


class Video(BaseModel):
    video_id = models.CharField(max_length=50)
    link = models.URLField()
    name = models.CharField(max_length=255)


class Reel(BaseModel):
    reel_id = models.CharField(max_length=50)
    link = models.URLField()
    name = models.CharField(max_length=255)


class Comment(BaseModel):
    comment_id = models.CharField(max_length=50)
    text = models.TextField()


@receiver(post_save, sender=OutSourcedInfo)
def initialize_account(sender, instance, created, **kwargs):

    if created:
        account = Account()
        account.outsourced = instance
        account.save()
        print(f"initialized outsourced account - {instance}")
