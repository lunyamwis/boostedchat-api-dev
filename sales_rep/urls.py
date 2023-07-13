from rest_framework.routers import DefaultRouter

from .views import SalesRepManager

router = DefaultRouter()
router.register(r"rep", SalesRepManager, basename="rep")


urlpatterns = router.urls
