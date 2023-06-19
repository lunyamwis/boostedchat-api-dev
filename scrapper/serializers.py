from rest_framework import serializers


class GmapSerializer(serializers.Serializer):
    email = serializers.EmailField()
