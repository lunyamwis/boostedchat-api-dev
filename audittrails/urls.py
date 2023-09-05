from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"entries", views.LogEntryViewset, basename="entries")

urlpatterns = router.urls
