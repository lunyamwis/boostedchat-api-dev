from django.urls import path

from . import views

urlpatterns = [
    path("", views.FallbackWebhook.as_view(), name="fallback_webhook"),
]
