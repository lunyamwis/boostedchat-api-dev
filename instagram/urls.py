from rest_framework.routers import DefaultRouter

from .views import AccountViewSet, CommentViewSet, HashTagViewSet, PhotoViewSet, ReelViewSet, StoryViewSet, VideoViewSet

router = DefaultRouter()
router.register(r"account", AccountViewSet, basename="account")
router.register(r"comment", CommentViewSet, basename="comment")
router.register(r"hashtag", HashTagViewSet, basename="hashtag")
router.register(r"photo", PhotoViewSet, basename="photo")
router.register(r"video", VideoViewSet, basename="video")
router.register(r"reel", ReelViewSet, basename="reel")
router.register(r"story", StoryViewSet, basename="story")

urlpatterns = router.urls
