from rest_framework import serializers
from django_celery_beat.models import PeriodicTask

# class PeriodicTaskSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PeriodicTask
#         # fields = '__all__'
#         fields = ['task']
class PeriodicTaskGetSerializer(serializers.ModelSerializer):
    class Meta:
        model = PeriodicTask
        fields = '__all__'
class PeriodicTaskGetSerializer(serializers.ModelSerializer):
     class Meta:
        model = PeriodicTask
        fields = '__all__'
class PeriodicTaskPostSerializer(serializers.Serializer):
     task = serializers.CharField(default="instagram.tasks.send_first_compliment")
     startTime = serializers.CharField(default=14)
     startMinute = serializers.CharField(default=0)
     numperDay = serializers.CharField(default=30)