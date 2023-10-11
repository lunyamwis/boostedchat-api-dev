from django.urls import path

from . import views
from instagram.views import initialize_db

urlpatterns = [
    path("fallbackWebhook/", views.FallbackWebhook.as_view()),
    path("needsAssessmentWebhook/", views.NeedsAssesmentWebhook.as_view()),
    path("init/", initialize_db, name="initialize_db")
]
