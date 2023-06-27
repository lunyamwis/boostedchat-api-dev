from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import GmapScrapper, GmapsProfiles, InstagramScrapper, StyleseatScrapper, StyleSeatScrapperProfiles

router = DefaultRouter()
router.register(r"styleseat", StyleSeatScrapperProfiles, basename="styleseat")
router.register(r"gmaps", GmapsProfiles, basename="gmaps")
router.register(r"instagram", InstagramScrapper, basename="instagram")
urlpatterns = router.urls


urlpatterns = [
    path("gmaps/", GmapScrapper.as_view(), name="gmaps_scrapper"),
    path("styleseat/", StyleseatScrapper.as_view(), name="styleseat_scrapper"),
    path("search/", InstagramScrapper.as_view({"post": "retrieve_gmap_users"})),
    path("profiles/", include(router.urls)),
]
