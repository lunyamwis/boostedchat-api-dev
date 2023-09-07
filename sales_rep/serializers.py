from rest_framework import serializers

from .models import SalesRep


class SalesRepSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesRep
        fields = ["id", "user", "ig_username", "ig_password", "instagram"]
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
            "instagram": {"required": False, "allow_null": True},
        }


class AccountAssignmentSerializer(serializers.Serializer):
    REACTIONS = ((1, "Comment"), (2, "Direct Messaging"), (3, "Like"))

    reaction = serializers.ChoiceField(choices=REACTIONS)
