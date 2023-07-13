from rest_framework import serializers

from .models import Lead


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = ["id", "instagram"]
        extra_kwargs = {"id": {"required": False, "allow_null": True}}
