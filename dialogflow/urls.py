from django.urls import path

from . import views

urlpatterns = [
    path("fallbackWebhook/", views.FallbackWebhook.as_view()),
    path("needsAssessmentWebhook/", views.NeedsAssesmentWebhook.as_view()),
]
