from rest_framework import serializers
from .models import ExceptionModel

class ExceptionSerializer(serializers.ModelSerializer):
     class Meta:
        model = ExceptionModel
        fields = '__all__'