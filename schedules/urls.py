from django.urls import path

from . import views


app_name = "schedules"


urlpatterns = [
    path(
        "callcenters/<str:codename>/horario/",
        views.schedule_editor,
        name="editor",
    ),
]
