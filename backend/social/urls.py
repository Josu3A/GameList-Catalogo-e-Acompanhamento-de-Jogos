from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('friendships', views.FriendshipViewSet, basename='friendship')
router.register('reviews', views.ReviewViewSet, basename='review')
router.register('lists', views.ListViewSet, basename='list')
router.register('notifications', views.NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
]
