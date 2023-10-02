# set serializers here

from rest_framework import serializers

from dialogflow.models import InstaLead, InstaMessage


class CreateLeadSerializer(serializers.ModelSerializer):
    """Serializer to create lead"""
    class Meta:
        model = InstaLead
        fields = "__all__"


class InstagramMessageSerializer(serializers.ModelSerializer):
    """Serializer to save and get a single Instagram Message"""
    class Meta:
        model = InstaMessage
        fields = "__all__"


class GetInstagramMessageSerializer(serializers.ModelSerializer):
    """Serializer to get all instagram messages"""
    class Meta:
        model = InstaMessage
        fields = "__all__"