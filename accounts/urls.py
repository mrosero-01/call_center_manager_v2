from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views


urlpatterns = [
    path(
        "login/",
        views.RateLimitedLoginView.as_view(),
        name="login",
    ),
    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
    ),
    path(
        "",
        views.home,
        name="home",
    ),
]
