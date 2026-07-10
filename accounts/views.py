from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from callcenters.selectors import get_callcenters_for_user
from schedules.models import ScheduleInterval, Weekday


WEEKDAY_ORDER = [
    Weekday.MONDAY,
    Weekday.TUESDAY,
    Weekday.WEDNESDAY,
    Weekday.THURSDAY,
    Weekday.FRIDAY,
    Weekday.SATURDAY,
    Weekday.SUNDAY,
]

WEEKDAY_SHORT_LABELS = {
    Weekday.MONDAY: "Lun",
    Weekday.TUESDAY: "Mar",
    Weekday.WEDNESDAY: "Mié",
    Weekday.THURSDAY: "Jue",
    Weekday.FRIDAY: "Vie",
    Weekday.SATURDAY: "Sáb",
    Weekday.SUNDAY: "Dom",
}


def _get_greeting():
    current_hour = timezone.localtime(
        timezone.now(),
    ).hour

    if 5 <= current_hour < 12:
        return "Buenos días"

    if 12 <= current_hour < 19:
        return "Buenas tardes"

    return "Buenas noches"


def _format_interval(interval):
    return (
        f"{interval.start_time:%H:%M}"
        "–"
        f"{interval.end_time:%H:%M}"
    )


def _build_schedule_preview(callcenter):
    grouped_intervals = {
        weekday: []
        for weekday in WEEKDAY_ORDER
    }

    for interval in callcenter.schedule_intervals.all():
        if interval.weekday in grouped_intervals:
            grouped_intervals[interval.weekday].append(interval)

    days = []

    for weekday in WEEKDAY_ORDER:
        intervals = sorted(
            grouped_intervals[weekday],
            key=lambda item: (
                item.start_time,
                item.end_time,
            ),
        )

        if not intervals:
            continue

        days.append(
            {
                "label": WEEKDAY_SHORT_LABELS[weekday],
                "summary": " · ".join(
                    _format_interval(interval)
                    for interval in intervals
                ),
            }
        )

    return {
        "days": days[:2],
        "extra_days": max(
            0,
            len(days) - 2,
        ),
        "has_schedule": bool(days),
    }


@login_required
def home(request):
    callcenters = get_callcenters_for_user(
        request.user,
    )
    preview_callcenters = (
        callcenters
        .prefetch_related("schedule_intervals")[:4]
    )

    callcenter_cards = []

    for callcenter in preview_callcenters:
        schedule_preview = _build_schedule_preview(callcenter)

        callcenter_cards.append(
            {
                "callcenter": callcenter,
                "schedule": schedule_preview,
            }
        )

    return render(
        request,
        "home.html",
        {
            "greeting": _get_greeting(),
            "dashboard_summary": {
                "callcenters": callcenters.count(),
                "active": callcenters.filter(
                    is_active=True,
                ).count(),
                "without_schedule": callcenters.filter(
                    schedule_intervals__isnull=True,
                ).count(),
            },
            "callcenter_cards": callcenter_cards,
        },
    )
