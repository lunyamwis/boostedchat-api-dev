from auditlog.models import LogEntry
from rest_framework import serializers


class LogEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LogEntry
        fields = "__all__"
        extra_kwargs = {"id": {"required": False, "allow_null": True}}
