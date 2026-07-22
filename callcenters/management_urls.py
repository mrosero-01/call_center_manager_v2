from django.urls import path

from . import management_views


app_name = "management"


urlpatterns = [
    path(
        "",
        management_views.configuration_dashboard,
        name="dashboard",
    ),
    path(
        "clientes/nuevo/",
        management_views.client_create,
        name="client_create",
    ),
    path(
        "clientes/<int:pk>/editar/",
        management_views.client_update,
        name="client_update",
    ),
    path(
        "callcenters/nuevo/",
        management_views.callcenter_create,
        name="callcenter_create",
    ),
    path(
        "callcenters/<int:pk>/editar/",
        management_views.callcenter_update,
        name="callcenter_update",
    ),
]
