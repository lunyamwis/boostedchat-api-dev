from rest_framework import serializers

from .models import Account, Comment, HashTag, Photo, Reel, Story, Video


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ["igname"]


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["comment_id", "text"]


class HashTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = HashTag
        fields = ["hashtag_id"]


class PhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ["id", "photo_id", "link", "name"]


class VideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Video
        fields = ["video_id", "link", "name"]


class ReelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reel
        fields = ["reel_id", "link", "name"]


class StorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Story
        fields = ["link"]


class UploadSerializer(serializers.Serializer):
    file_uploaded = serializers.FileField()

    class Meta:
        fields = ["file_uploaded"]
