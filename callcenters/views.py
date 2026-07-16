from django.contrib.auth.decorators import login_required
from django.db.models import Exists, OuterRef, Subquery
from django.shortcuts import render

from schedules.models import ScheduleChangeLog, ScheduleInterval

from .selectors import get_callcenters_for_user


@login_required
def callcenter_list(request):
    latest_change = (
        ScheduleChangeLog.objects
        .filter(callcenter=OuterRef("pk"))
        .order_by("-created_at")
    )
    callcenters = (
        get_callcenters_for_user(request.user)
        .annotate(
            has_schedule=Exists(
                ScheduleInterval.objects.filter(
                    callcenter=OuterRef("pk"),
                )
            ),
            latest_change_at=Subquery(
                latest_change.values("created_at")[:1],
            ),
            latest_change_reason=Subquery(
                latest_change.values("reason")[:1],
            ),
        )
    )

    return render(
        request,
        "callcenters/callcenter_list.html",
        {
            "callcenters": callcenters,
        },
    )
