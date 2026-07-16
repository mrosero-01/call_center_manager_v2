from django.contrib.auth.views import LogoutView
from django.urls import path
from django.views.generic import RedirectView

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
        RedirectView.as_view(
            pattern_name="callcenters:list",
            permanent=False,
        ),
        name="root",
    ),
]
