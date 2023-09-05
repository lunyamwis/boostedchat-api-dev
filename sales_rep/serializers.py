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
    per_sales_rep = serializers.IntegerField()
