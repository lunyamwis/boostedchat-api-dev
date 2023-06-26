from rest_framework import serializers


class GmapSerializer(serializers.Serializer):
    specific_element = serializers.CharField(max_length=255)
    css_selector_search_box = serializers.CharField(max_length=255)
    area_of_search = serializers.CharField(max_length=50)
    search_button = serializers.CharField(max_length=255)
    delay = serializers.IntegerField()


class StyleseatSerializer(serializers.Serializer):
    css_selector_service_box = serializers.CharField(max_length=255)
    css_selector_area_box = serializers.CharField(max_length=255)
    css_selector_submit_btn = serializers.CharField(max_length=255)
    css_selector_seats = serializers.CharField(max_length=255)
    xpath_name = serializers.CharField(max_length=255)
    xpath_popup = serializers.CharField(max_length=255)
    service = serializers.CharField(max_length=255)
    area = serializers.CharField(max_length=255)
    delay = serializers.IntegerField()


class StyleseatProfileSerializer(serializers.Serializer):
    xpath_ig_username = serializers.CharField(max_length=255)
    xpath_review = serializers.CharField(max_length=255)


class GmapsProfileSerializer(serializers.Serializer):
    xpath_business = serializers.CharField(max_length=255)
    xpath_review = serializers.CharField(max_length=255)
