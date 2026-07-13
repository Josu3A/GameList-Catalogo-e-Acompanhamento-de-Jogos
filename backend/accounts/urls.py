from django.urls import path

from . import views

urlpatterns = [
    path('csrf/', views.csrf_view, name='auth-csrf'),
    path('register/', views.RegisterView.as_view(), name='auth-register'),
    path('login/', views.LoginView.as_view(), name='auth-login'),
    path('logout/', views.LogoutView.as_view(), name='auth-logout'),
    path('me/', views.MeView.as_view(), name='auth-me'),
    # Integração Steam (OpenID 2.0 — só vincula/loga, nunca cria conta)
    path('steam/login/', views.steam_login, name='auth-steam-login'),
    path('steam/callback/', views.steam_callback, name='auth-steam-callback'),
    path('steam/disconnect/', views.SteamDisconnectView.as_view(), name='auth-steam-disconnect'),
]
