from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import GmapScrapper, StyleseatScrapper, StyleSeatScrapperProfiles

router = DefaultRouter()
router.register(r"styleseat", StyleSeatScrapperProfiles, basename="profiles")
urlpatterns = router.urls


urlpatterns = [
    path("gmaps/", GmapScrapper.as_view(), name="gmaps_scrapper"),
    path("styleseat/", StyleseatScrapper.as_view(), name="styleseat_scrapper"),
    path("profiles/", include(router.urls)),
    # path("profile/",StyleSeatScrapperProfiles.as_view({'get': 'retrieve'})),
]
