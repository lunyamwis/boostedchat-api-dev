from rest_framework import serializers

from .models import Account, OutSourced, Comment, HashTag, Photo, Reel, Story, Thread, Video, Message, StatusCheck, OutSourced
from django_celery_beat.models import PeriodicTask


class OutSourcedSerializer(serializers.ModelSerializer):
    class Meta:
        model = OutSourced
        fields = '__all__'
        extra_kwargs = {"id": {"required": False, "allow_null": True}}

class AccountSerializer(serializers.ModelSerializer):
    # account_history = serializers.CharField(source="history.latest",read_only=True)
    # print(account_history)
    class Meta:
        model = Account
        fields = [
            "id",
            "igname",
            "full_name",
        ]
        extra_kwargs = {"id": {"required": False, "allow_null": True}}


class GetAccountSerializer(serializers.ModelSerializer):
    # status = serializers.CharField(source="account.status.name", read_only=True)
    class Meta:
        model = Account
        fields = '__all__'
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            status_ = StatusCheck.objects.get(id=data['status'])
            data['status'] = status_.name
        except Exception as error:
            print(error)
        try:
            periodic_task = PeriodicTask.objects.get(name=f"SendFirstCompliment-{instance.igname}")
            data['outreach'] = periodic_task.crontab.human_readable 
        except PeriodicTask.DoesNotExist:
            pass
        return data
    
class ScheduleOutreachSerializer(serializers.Serializer):
    minute = serializers.CharField()
    hour = serializers.CharField()
    day_of_week = serializers.CharField()
    day_of_month = serializers.CharField()
    month_of_year = serializers.CharField()
    class Meta:
        fields = '__all__'

class GetSingleAccountSerializer(serializers.ModelSerializer):
    # status = serializers.CharField(source="account.status.name", read_only=True)
    class Meta:
        model = Account
        fields = '__all__'
        extra_kwargs = {
            "id": {"required": False, "allow_null": True},
        }

    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            status_ = StatusCheck.objects.get(id=data['status'])
            data['status'] = status_.name
        except Exception as error:
            print(error)

        try:
            data['outsourced'] = OutSourced.objects.get(account__id=data['id']).results
        except Exception as error:
            print(error)
        try:
            periodic_task = PeriodicTask.objects.get(name=f"SendFirstCompliment-{instance.igname}")
            data['outreach'] = periodic_task.crontab.human_readable 
        except PeriodicTask.DoesNotExist:
            pass

        return data


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "comment_id", "text"]
        extra_kwargs = {"id": {"required": False, "allow_null": True}}


class HashTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = HashTag
        fields = ["id", "hashtag_id"]
        extra_kwargs = {"id": {"required": False, "allow_null": True}}


class PhotoSerializer(serializers.ModelSerializer):
    account_username = serializers.CharField(source="account.igname", read_only=True)

    class Meta:
        model = Photo
        fields = ["id", "photo_id", "link", "name", "account_username"]
        extra_kwargs = {"id": {"required": False, "allow_null": True}}


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ["id", "video_id", "link", "name"]
        extra_kwargs = {"id": {"required": False, "allow_null": True}}


class ReelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reel
        fields = ["id", "reel_id", "link", "name"]
        extra_kwargs = {"id": {"required": False, "allow_null": True}}


class StorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Story
        fields = ["id", "link"]
        extra_kwargs = {"id": {"required": False, "allow_null": True}}


class UploadSerializer(serializers.Serializer):
    file_uploaded = serializers.FileField()

    class Meta:
        fields = ["file_uploaded"]


class AddContentSerializer(serializers.Serializer):
    assign_robot = serializers.BooleanField(default=True)
    approve = serializers.BooleanField(default=False)
    text = serializers.CharField(max_length=255, required=False)
    human_response = serializers.CharField(max_length=1024, required=False)
    generated_response = serializers.CharField(max_length=1024, required=False)


class SendManualMessageSerializer(serializers.Serializer):
    assigned_to = serializers.CharField(default="Robot")
    message = serializers.CharField(required=False)


class GenerateMessageInputSerializer(serializers.Serializer):
    thread_id = serializers.CharField(required=True)
    message = serializers.CharField(required=True)


class ThreadSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="account.igname", read_only=True)
    assigned_to = serializers.CharField(source="account.assigned_to", read_only=True)
    account_id = serializers.CharField(source="account.id", read_only=True)
    stage = serializers.CharField(source="account.index", read_only=True)
    
    class Meta:
        model = Thread
        fields = ["id", "username", "thread_id", "assigned_to", "account_id",
                  "unread_message_count", "last_message_content", "stage", "last_message_at",]
        extra_kwargs = {"id": {"required": False, "allow_null": True},
                        "account": {"required": False, "allow_null": True}}


    def to_representation(self, instance):
        data = super().to_representation(instance)
        try:
            data['salesrep'] = instance.account.salesrep_set.last().ig_username
        except Exception as error:
            print(error)
        return data

class SingleThreadSerializer(serializers.ModelSerializer):

    class Meta:
        model = Thread
        fields = "__all__"


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = "__all__"
        extra_kwargs = {"id": {"required": False, "allow_null": True},
                        "sent_on": {"required": False, "allow_null": True}}        
