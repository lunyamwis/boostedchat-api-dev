from rest_framework import serializers


class GmapSerializer(serializers.Serializer):
    area_of_search = serializers.CharField(max_length=255)


class StyleseatSerializer(serializers.Serializer):
    service = serializers.CharField(max_length=255)
    area = serializers.CharField(max_length=255)
