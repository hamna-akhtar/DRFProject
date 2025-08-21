from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views



router = DefaultRouter()
router.register(r'journals', views.JournalEntryViewSet, basename='journal')
router.register(r'users', views.UserViewSet, basename='customuser')
router.register(r'friend_requests', views.FriendRequestViewSet, basename='friendrequest')


# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include(router.urls)),
]