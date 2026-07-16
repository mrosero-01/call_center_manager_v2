from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    path(
        "auditoria/",
        include("audit.urls"),
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
