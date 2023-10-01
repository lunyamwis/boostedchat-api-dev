# Create your models here.
# models.py

import uuid
from django.db import models


class RequestTracker(models.Model):
    request_count = models.PositiveIntegerField(default=0)


class InstaLead(models.Model):
    class LeadStatus(models.IntegerChoices):
        SENDING_COMPLIMENT = 1
        SENDING_NEEDS_ASSESSMENT_QUESTIONS = 2
        SENDING_SOLUTION_TO_PROBLEMS = 3
        RESOLVING_OBJECTIONS = 4
        ACTIVATING = 5
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True)
    igname = models.TextField(unique=True)
    thread_id = models.TextField(null=True)
    booking_system = models.TextField(null=True)
    calendar_availability = models.TextField(null=True)
    social_media_activity = models.TextField(null=True)
    ig_book_button = models.TextField(null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    is_engaged = models.BooleanField(default=False)
    status = models.IntegerField(choices=LeadStatus.choices, default=1)


class InstaMessage(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True)
    content = models.TextField()
    lead_id = models.ForeignKey(
        InstaLead, on_delete=models.CASCADE)
    sent_by = models.TextField()
    sent_on = models.DateTimeField()
