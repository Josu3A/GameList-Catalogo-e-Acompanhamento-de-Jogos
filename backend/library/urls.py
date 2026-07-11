from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('my-games', views.UserGameViewSet, basename='my-games')

urlpatterns = [
    path('', include(router.urls)),
    path('profiles/<int:user_id>/', views.ProfileView.as_view(), name='profile'),
]
