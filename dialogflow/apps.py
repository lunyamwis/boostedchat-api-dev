from django.apps import AppConfig
from django.core.signals import request_finished


class DialogflowConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "dialogflow"

    def ready(self):
        # Implicitly connect signal handlers decorated with @receiver.
        from . import signals

        # Explicitly connect a signal handler.
        request_finished.connect(signals.update_request_count)
