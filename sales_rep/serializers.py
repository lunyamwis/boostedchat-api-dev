from rest_framework import serializers

from .models import SalesRep


class SalesRepSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesRep
        fields = ["id", "user"]
        extra_kwargs = {"id": {"required": False, "allow_null": True}}
