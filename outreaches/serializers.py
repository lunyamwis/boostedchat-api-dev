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
     startTime = serializers.IntegerField(default=14) #set to int
     startMinute = serializers.IntegerField(default=0) #set to int
     numperDay = serializers.IntegerField(default=30)#set to int
     user = serializers.CharField(default=30)

class SingleTask(serializers.Serializer):
     task = serializers.CharField(default="instagram.tasks.send_first_compliment")