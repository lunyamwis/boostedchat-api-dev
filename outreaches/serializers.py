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

class TaskBySalesRepSerializer(serializers.Serializer):
    task = serializers.ChoiceField(choices=["instagram.tasks.send_first_compliment"])
    sales_rep = serializers.CharField(required=True)
    status = serializers.ChoiceField(choices=["any", "enabled", "disabled"], default="any")
    order = serializers.ChoiceField(choices=[1,-1])
    number = serializers.IntegerField(default=-1)
    
class FirstComplimentViewSet(serializers.Serializer):
    task = serializers.ChoiceField(choices=["instagram.tasks.send_first_compliment"])
    user = serializers.CharField(required=True)
    # we will need to modify later to choose the sales_rep as well