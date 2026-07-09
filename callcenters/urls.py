from django.urls import path

from . import views


app_name = "callcenters"


urlpatterns = [
    path(
        "",
        views.callcenter_list,
        name="list",
    ),
]
