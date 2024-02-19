from rest_framework.routers import DefaultRouter

from .views import LeadManager

router = DefaultRouter()
router.register(r"", LeadManager, basename="leads")


urlpatterns = router.urls
