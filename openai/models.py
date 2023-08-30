from django.db import models

from base.models import BaseModel
from dialogflow.models import ScriptStage


class Prompt(BaseModel):
    prompt = models.TextField()
    stage = models.ForeignKey(ScriptStage, on_delete=models.CASCADE, null=True, blank=True)
