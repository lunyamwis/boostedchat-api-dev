from rest_framework.routers import DefaultRouter
from django.urls import path,include

from .views import (
    AccountViewSet,
    CommentViewSet,
    DMViewset,
    HashTagViewSet,
    MessageViewSet,
    PhotoViewSet,
    ReelViewSet,
    StoryViewSet,
    VideoViewSet,
    update_thread_details,
)

router = DefaultRouter()
router.register(r"account", AccountViewSet, basename="account")
router.register(r"comment", CommentViewSet, basename="comment")
router.register(r"hashtag", HashTagViewSet, basename="hashtag")
router.register(r"photo", PhotoViewSet, basename="photo")
router.register(r"video", VideoViewSet, basename="video")
router.register(r"reel", ReelViewSet, basename="reel")
router.register(r"story", StoryViewSet, basename="story")
router.register(r"dm", DMViewset, basename="dm")
router.register(r"message", MessageViewSet, basename="message")
urlpatterns = router.urls

urlpatterns = [
    path("", include(router.urls)),
    path(
        'dflow/<str:thread_id>/generate-response/',
        DMViewset.as_view({'post': 'generate_response'}),
        name='generate_response',
    ),
    path(
        'fallback/<str:thread_id>/assign-operator/',
        DMViewset.as_view({'post': 'assign_operator'}),
        name='assign_operator',
    ),
    path(
        'dm/messages-by-ig-thread/<str:ig_thread_id>/',
        DMViewset.as_view({'get': 'messages_by_ig_thread_id'}),
        name='messages_by_ig_thread_id',
    ),
    path(
        'dm/thread-by-ig-thread/<str:ig_thread_id>/',
        DMViewset.as_view({'get': 'thread_by_ig_thread_id'}),
        name='thread_by_ig_thread_id',
    ),
    path(
        'account/account-by-ig-thread/<str:ig_thread_id>/',
        AccountViewSet.as_view({'get': 'account_by_ig_thread_id'}),
        name='account_by_ig_thread_id',
    ),
    path(
        'update-thread-details/',
        update_thread_details
    )

]

