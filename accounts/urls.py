from django.contrib.auth.views import LogoutView
from django.urls import path
from django.views.generic import RedirectView

from . import management_views
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
        "usuarios/",
        management_views.user_list,
        name="user_list",
    ),
    path(
        "usuarios/crear/",
        management_views.user_create,
        name="user_create",
    ),
    path(
        "usuarios/nuevo/",
        RedirectView.as_view(
            pattern_name="user_create",
            permanent=False,
        ),
    ),
    path(
        "usuarios/<int:pk>/editar/",
        management_views.user_update,
        name="user_update",
    ),
    path(
        "usuarios/<int:pk>/password/",
        management_views.user_password_update,
        name="user_password_update",
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
