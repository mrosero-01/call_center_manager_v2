from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from clients.models import Client

from .forms import (
    CallCenterCreateForm,
    CallCenterUpdateForm,
    ClientForm,
)
from .models import CallCenter


def _require_superuser(request):
    if not request.user.is_superuser:
        raise PermissionDenied(
            "No tienes permiso para administrar la configuración.",
        )


@login_required
def configuration_dashboard(request):
    _require_superuser(request)

    clients = list(
        Client.objects
        .prefetch_related(
            "callcenters",
            "user_set",
        )
        .order_by("name")
    )
    callcenters = (
        CallCenter.objects
        .select_related("client")
        .order_by("client__name", "name")
    )

    return render(
        request,
        "configuration/dashboard.html",
        {
            "clients": clients,
            "callcenters": callcenters,
            "active_client_count": sum(
                client.is_active
                for client in clients
            ),
            "active_callcenter_count": callcenters.filter(
                is_active=True,
            ).count(),
        },
    )


@login_required
def client_create(request):
    _require_superuser(request)
    form = ClientForm(
        request.POST or None,
    )

    if request.method == "POST" and form.is_valid():
        client = form.save()
        messages.success(
            request,
            f"Cliente {client.name} creado correctamente.",
        )
        return redirect("management:dashboard")

    return render(
        request,
        "configuration/client_form.html",
        {
            "form": form,
            "title": "Crear cliente",
            "submit_label": "Crear cliente",
            "is_create": True,
        },
    )


@login_required
def client_update(request, pk):
    _require_superuser(request)
    client = get_object_or_404(
        Client,
        pk=pk,
    )
    form = ClientForm(
        request.POST or None,
        instance=client,
    )

    if request.method == "POST" and form.is_valid():
        client = form.save()
        messages.success(
            request,
            f"Cliente {client.name} actualizado.",
        )
        return redirect("management:dashboard")

    return render(
        request,
        "configuration/client_form.html",
        {
            "form": form,
            "title": f"Editar cliente {client.name}",
            "submit_label": "Guardar cambios",
            "managed_client": client,
            "is_create": False,
        },
    )


@login_required
def callcenter_create(request):
    _require_superuser(request)
    initial = {}

    if request.GET.get("client"):
        initial["client"] = request.GET["client"]

    form = CallCenterCreateForm(
        request.POST or None,
        initial=initial,
    )

    if request.method == "POST" and form.is_valid():
        callcenter = form.save()
        messages.success(
            request,
            f"CallCenter {callcenter.name} creado correctamente.",
        )
        return redirect("management:dashboard")

    return render(
        request,
        "configuration/callcenter_form.html",
        {
            "form": form,
            "title": "Crear CallCenter",
            "submit_label": "Crear CallCenter",
            "is_create": True,
        },
    )


@login_required
def callcenter_update(request, pk):
    _require_superuser(request)
    callcenter = get_object_or_404(
        CallCenter.objects.select_related("client"),
        pk=pk,
    )
    form = CallCenterUpdateForm(
        request.POST or None,
        instance=callcenter,
    )

    if request.method == "POST" and form.is_valid():
        callcenter = form.save()
        messages.success(
            request,
            f"CallCenter {callcenter.name} actualizado.",
        )
        return redirect("management:dashboard")

    return render(
        request,
        "configuration/callcenter_form.html",
        {
            "form": form,
            "title": f"Editar CallCenter {callcenter.name}",
            "submit_label": "Guardar cambios",
            "callcenter": callcenter,
            "is_create": False,
        },
    )
