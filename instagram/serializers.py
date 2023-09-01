from rest_framework import serializers

from .models import Account, Comment, HashTag, Photo, Reel, Story, Video


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ["id", "igname"]
        extra_kwargs = {"id": {"required": False, "allow_null": True}}


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
    class Meta:
        model = Photo
        fields = ["id", "photo_id", "link", "name"]
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


class AddCommentSerializer(serializers.Serializer):
    assign_robot = serializers.BooleanField(default=True)
    approve = serializers.BooleanField(default=False)
    text = serializers.CharField(max_length=255, required=False)
    human_response = serializers.CharField(max_length=255, required=False)
    generated_response = serializers.CharField(max_length=255, required=False)
