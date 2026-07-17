from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from clients.models import Client

from .forms import (
    ManagedUserCreateForm,
    ManagedUserPasswordForm,
    ManagedUserUpdateForm,
)


def _forbid_non_superuser(request):
    if request.user.is_superuser:
        return None

    raise PermissionDenied(
        "No tienes permiso para administrar usuarios.",
    )


def _managed_users():
    return (
        get_user_model().objects
        .filter(
            is_superuser=False,
            is_staff=False,
        )
        .select_related("client")
        .annotate(
            callcenter_count=Count(
                "client__callcenters",
                distinct=True,
            ),
        )
        .order_by("username")
    )


def _get_managed_user(pk):
    return get_object_or_404(
        _managed_users(),
        pk=pk,
    )


def _get_client_callcenters(client):
    if not client:
        return []

    return client.callcenters.order_by("name")


def _client_callcenter_map():
    clients = (
        Client.objects
        .prefetch_related("callcenters")
        .order_by("name")
    )

    return {
        str(client.pk): [
            {
                "name": callcenter.name,
                "codename": callcenter.codename,
                "is_active": callcenter.is_active,
            }
            for callcenter in client.callcenters.all()
        ]
        for client in clients
    }


def _selected_client_from_form(form, fallback=None):
    client_id = form.data.get("client")

    if client_id:
        return Client.objects.filter(pk=client_id).first()

    return fallback


@login_required
def user_list(request):
    forbidden_response = _forbid_non_superuser(request)

    if forbidden_response:
        return forbidden_response

    filters = {
        "q": request.GET.get("q", "").strip(),
        "client": request.GET.get("client", ""),
        "status": request.GET.get("status", ""),
    }
    users = _managed_users()
    has_managed_users = users.exists()

    if filters["q"]:
        users = users.filter(
            Q(username__icontains=filters["q"])
            | Q(first_name__icontains=filters["q"])
            | Q(last_name__icontains=filters["q"])
            | Q(email__icontains=filters["q"])
        )

    if filters["client"]:
        users = users.filter(
            client_id=filters["client"],
        )

    if filters["status"] == "active":
        users = users.filter(is_active=True)
    elif filters["status"] == "inactive":
        users = users.filter(is_active=False)

    paginator = Paginator(
        users,
        20,
    )
    page = paginator.get_page(
        request.GET.get("page"),
    )
    query_params = request.GET.copy()
    query_params.pop(
        "page",
        None,
    )

    return render(
        request,
        "accounts/user_list.html",
        {
            "users": page,
            "filters": filters,
            "clients": Client.objects.order_by("name"),
            "total_count": users.count(),
            "has_managed_users": has_managed_users,
            "query_string": query_params.urlencode(),
        },
    )


@login_required
def user_create(request):
    forbidden_response = _forbid_non_superuser(request)

    if forbidden_response:
        return forbidden_response

    if request.method == "POST":
        form = ManagedUserCreateForm(request.POST)

        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"Usuario {user.username} creado correctamente.",
            )

            return redirect("user_list")
    else:
        form = ManagedUserCreateForm()

    selected_client = _selected_client_from_form(form)

    return render(
        request,
        "accounts/user_form.html",
        {
            "form": form,
            "title": "Crear usuario",
            "submit_label": "Crear usuario",
            "selected_client": selected_client,
            "client_callcenters": _get_client_callcenters(
                selected_client,
            ),
            "client_callcenter_map": _client_callcenter_map(),
            "is_create": True,
        },
    )


@login_required
def user_update(request, pk):
    forbidden_response = _forbid_non_superuser(request)

    if forbidden_response:
        return forbidden_response

    user = _get_managed_user(pk)

    if request.method == "POST":
        form = ManagedUserUpdateForm(
            request.POST,
            instance=user,
        )

        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f"Usuario {user.username} actualizado.",
            )

            return redirect("user_list")
    else:
        form = ManagedUserUpdateForm(instance=user)

    selected_client = _selected_client_from_form(
        form,
        fallback=user.client,
    )

    return render(
        request,
        "accounts/user_form.html",
        {
            "form": form,
            "title": f"Editar usuario {user.username}",
            "submit_label": "Guardar cambios",
            "managed_user": user,
            "selected_client": selected_client,
            "client_callcenters": _get_client_callcenters(
                selected_client,
            ),
            "client_callcenter_map": _client_callcenter_map(),
            "is_create": False,
        },
    )


@login_required
def user_password_update(request, pk):
    forbidden_response = _forbid_non_superuser(request)

    if forbidden_response:
        return forbidden_response

    user = _get_managed_user(pk)

    if request.method == "POST":
        form = ManagedUserPasswordForm(
            user,
            request.POST,
        )

        if form.is_valid():
            form.save()
            messages.success(
                request,
                f"Contraseña de {user.username} actualizada.",
            )

            return redirect("user_update", pk=user.pk)
    else:
        form = ManagedUserPasswordForm(user)

    return render(
        request,
        "accounts/user_password_form.html",
        {
            "form": form,
            "managed_user": user,
        },
    )
