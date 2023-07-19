from rest_framework import serializers
from authentication.models import User

from authentication.serializers import UserListSerializer

from .models import SalesRep


class SalesRepSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesRep
        fields = ["id", "user", "instagram"]
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
            "instagram": {"required": False, "allow_null": True},
        }


class SalesRepListSerializer(serializers.ModelSerializer):

    user = serializers.SerializerMethodField()

    def get_user(self, obj):
        userId = obj.user
        try:
            qs = User.objects.get(pk=userId)
            return UserListSerializer(qs).data
        except Exception:
            return None

    class Meta:
        model = SalesRep
        fields = ["id", "user", "instagram"]
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
            "instagram": {"required": False, "allow_null": True},
        }


class AccountAssignmentSerializer(serializers.Serializer):
    per_sales_rep = serializers.IntegerField()
