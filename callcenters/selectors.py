from django.shortcuts import get_object_or_404

from .models import CallCenter


def get_callcenters_for_user(user):
    queryset = (
        CallCenter.objects
        .select_related("client")
        .order_by("name")
    )

    if user.is_superuser:
        return queryset

    if user.client_id is None:
        return queryset.none()

    return queryset.filter(
        client_id=user.client_id,
        client__is_active=True,
        is_active=True,
    )


def get_callcenter_for_user(user, codename):
    queryset = get_callcenters_for_user(user)

    return get_object_or_404(
        queryset,
        codename=codename,
    )
