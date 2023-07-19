from allauth.socialaccount.providers.facebook.views import FacebookOAuth2Adapter
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from allauth.socialaccount.providers.twitter.views import TwitterOAuthAdapter
from dj_rest_auth.registration.views import SocialLoginView
from dj_rest_auth.social_serializers import TwitterLoginSerializer
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import UserListSerializer, UserLoginSerializer, UserRegistrationSerializer


class TwitterLogin(SocialLoginView):
    serializer_class = TwitterLoginSerializer
    adapter_class = TwitterOAuthAdapter


class FacebookLogin(SocialLoginView):
    adapter_class = FacebookOAuth2Adapter


class GoogleLogin(SocialLoginView):  # if you want to use Implicit Grant, use this
    adapter_class = GoogleOAuth2Adapter


class AuthUserRegistrationView(APIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        valid = serializer.is_valid(raise_exception=True)

        if valid:
            serializer.save()
            status_code = status.HTTP_201_CREATED

            response = {
                "success": True,
                "statusCode": status_code,
                "message": "User successfully registered!",
                "user": serializer.data,
            }

            return Response(response, status=status_code)


class AuthUserLoginView(APIView):
    serializer_class = UserLoginSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        valid = serializer.is_valid(raise_exception=True)

        if valid:
            status_code = status.HTTP_200_OK

            response = {
                "success": True,
                "statusCode": status_code,
                "message": "User logged in successfully",
                "access": serializer.data["access"],
                "refresh": serializer.data["refresh"],
                "authenticatedUser": {"email": serializer.data["email"], "role": serializer.data["role"]},
            }

            return Response(response, status=status_code)


class UserListView(APIView):
    serializer_class = UserListSerializer
    permission_classes = (AllowAny,)

    def get(self, request):
        users = User.objects.all()
        serializer = self.serializer_class(users, many=True)
        response = {
            "success": True,
            "status_code": status.HTTP_200_OK,
            "message": "Successfully fetched users",
            "users": serializer.data,
        }
        return Response(response, status=status.HTTP_200_OK)
