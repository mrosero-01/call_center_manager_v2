from django.contrib import admin
from django.conf import settings
from django.urls import include, path

from . import views


handler403 = "config.views.permission_denied"
handler404 = "config.views.page_not_found"


urlpatterns = [
    path("health/", views.healthcheck, name="healthcheck"),
    path(
        "auditoria/",
        include("audit.urls"),
    ),

    path(
        "configuracion/",
        include("callcenters.management_urls"),
    ),

    path(
        "callcenters/",
        include("callcenters.urls"),
    ),

    path(
        "",
        include("schedules.urls"),
    ),

    path("", include("accounts.urls")),
]

if settings.ENABLE_DJANGO_ADMIN:
    urlpatterns.insert(
        0,
        path("admin/", admin.site.urls),
    )
