from rest_framework import serializers


class GmapSerializer(serializers.Serializer):
    specific_element = serializers.TextField()
    css_selector_search_box = serializers.CharField(max_length=255)
    area_of_search = serializers.CharField(max_length=50)
    delay = serializers.IntegerField()
