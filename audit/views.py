from datetime import datetime, time

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.dateparse import parse_date

from callcenters.models import CallCenter
from schedules.audit import (
    get_schedule_change_summary,
    get_snapshot_days,
)
from schedules.models import ScheduleChangeLog


def _display_user(user):
    if not user:
        return "Usuario eliminado"

    return user.get_full_name() or user.username


def _date_boundary(value, boundary):
    parsed_date = parse_date(value or "")

    if not parsed_date:
        return None

    naive_datetime = datetime.combine(
        parsed_date,
        boundary,
    )

    return timezone.make_aware(
        naive_datetime,
        timezone.get_current_timezone(),
    )


@login_required
def audit_list(request):
    if not request.user.is_superuser:
        raise PermissionDenied(
            "No tienes permiso para ver la auditoría.",
        )

    filters = {
        "q": request.GET.get("q", "").strip(),
        "callcenter": request.GET.get("callcenter", ""),
        "user": request.GET.get("user", ""),
        "date_from": request.GET.get("date_from", ""),
        "date_to": request.GET.get("date_to", ""),
    }

    logs = (
        ScheduleChangeLog.objects
        .select_related(
            "callcenter",
            "user",
        )
        .all()
    )

    if filters["q"]:
        logs = logs.filter(
            reason__icontains=filters["q"],
        )

    if filters["callcenter"]:
        logs = logs.filter(
            callcenter_id=filters["callcenter"],
        )

    if filters["user"]:
        logs = logs.filter(
            user_id=filters["user"],
        )

    date_from = _date_boundary(
        filters["date_from"],
        time.min,
    )
    date_to = _date_boundary(
        filters["date_to"],
        time.max,
    )

    if date_from:
        logs = logs.filter(
            created_at__gte=date_from,
        )

    if date_to:
        logs = logs.filter(
            created_at__lte=date_to,
        )

    paginator = Paginator(
        logs,
        20,
    )
    page = paginator.get_page(
        request.GET.get("page"),
    )

    for log in page:
        log.change_summary = get_schedule_change_summary(
            log.before_snapshot,
            log.after_snapshot,
        )

    query_params = request.GET.copy()
    query_params.pop(
        "page",
        None,
    )

    return render(
        request,
        "audit/audit_list.html",
        {
            "logs": page,
            "filters": filters,
            "callcenters": CallCenter.objects.order_by(
                "name",
            ),
            "users": (
                get_user_model().objects
                .filter(schedule_change_logs__isnull=False)
                .distinct()
                .order_by("username")
            ),
            "total_count": logs.count(),
            "query_string": query_params.urlencode(),
        },
    )


@login_required
def audit_detail(request, pk):
    if not request.user.is_superuser:
        raise PermissionDenied(
            "No tienes permiso para ver la auditoría.",
        )

    change_log = get_object_or_404(
        ScheduleChangeLog.objects.select_related(
            "callcenter",
            "user",
        ),
        pk=pk,
    )

    return render(
        request,
        "audit/audit_detail.html",
        {
            "change_log": change_log,
            "display_user": _display_user(
                change_log.user,
            ),
            "before_days": get_snapshot_days(
                change_log.before_snapshot,
            ),
            "after_days": get_snapshot_days(
                change_log.after_snapshot,
            ),
        },
    )
