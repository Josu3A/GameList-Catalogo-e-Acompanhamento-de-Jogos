from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('games', views.GameViewSet, basename='game')
router.register('genres', views.GenreViewSet)
router.register('platforms', views.PlatformViewSet)
router.register('developers', views.DeveloperViewSet)
router.register('publishers', views.PublisherViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
