from django.contrib import admin
from django.urls import include, path


handler403 = "config.views.permission_denied"
handler404 = "config.views.page_not_found"


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
