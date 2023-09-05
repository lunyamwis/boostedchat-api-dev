from auditlog.models import LogEntry
from rest_framework import status, viewsets
from rest_framework.response import Response

from .serializers import LogEntrySerializer

# Create your views here.


class LogEntryViewset(viewsets.ModelViewSet):
    """
    A viewset that provides the standard actions
    """

    queryset = LogEntry.objects.all()
    serializer_class = LogEntrySerializer

    def list(self, request, *args, **kwargs):
        entries = []
        for entry in self.queryset:
            entry_dict = {
                "object_pk": entry.object_pk,
                "timestamp": entry.timestamp,
                "actor": f"{entry.actor.first_name} {entry.actor.last_name}",
                "actor_email": entry.actor.email,
                "action": entry.action,
                "changes": entry.changes,
            }
            entries.append(entry_dict)

        return Response(entries, status=status.HTTP_200_OK)
