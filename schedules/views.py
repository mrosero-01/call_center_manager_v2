from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render

from callcenters.selectors import get_callcenter_for_user

from .models import ScheduleChangeLog, ScheduleInterval, Weekday


WEEKDAYS = [
    {
        "value": Weekday.MONDAY,
        "label": "Lunes",
    },
    {
        "value": Weekday.TUESDAY,
        "label": "Martes",
    },
    {
        "value": Weekday.WEDNESDAY,
        "label": "Miércoles",
    },
    {
        "value": Weekday.THURSDAY,
        "label": "Jueves",
    },
    {
        "value": Weekday.FRIDAY,
        "label": "Viernes",
    },
    {
        "value": Weekday.SATURDAY,
        "label": "Sábado",
    },
    {
        "value": Weekday.SUNDAY,
        "label": "Domingo",
    },
]


WEEKDAY_LABELS = {
    day["value"]: day["label"]
    for day in WEEKDAYS
}


def _time_to_string(value):
    return value.strftime("%H:%M")


def _build_weekly_sections(rows):
    grouped = {
        day["value"]: []
        for day in WEEKDAYS
    }

    for row in rows:
        weekday = row["weekday"]

        if weekday not in grouped:
            continue

        grouped[weekday].append(
            {
                "start_time": row["start_time"],
                "end_time": row["end_time"],
            }
        )

    return [
        {
            "value": day["value"],
            "label": day["label"],
            "intervals": sorted(
                grouped[day["value"]],
                key=lambda item: item["start_time"],
            ),
        }
        for day in WEEKDAYS
    ]


def _build_schedule_summary(weekly_sections):
    open_days = [
        day
        for day in weekly_sections
        if day["intervals"]
    ]

    interval_count = sum(
        len(day["intervals"])
        for day in weekly_sections
    )

    return {
        "open_days": len(open_days),
        "closed_days": len(WEEKDAYS) - len(open_days),
        "interval_count": interval_count,
    }


def _get_schedule_rows(callcenter):
    intervals = (
        ScheduleInterval.objects
        .filter(callcenter=callcenter)
        .order_by(
            "start_time",
            "end_time",
        )
    )

    return [
        {
            "weekday": interval.weekday,
            "start_time": _time_to_string(
                interval.start_time,
            ),
            "end_time": _time_to_string(
                interval.end_time,
            ),
        }
        for interval in intervals
    ]


def _get_latest_change(callcenter):
    latest_change = (
        ScheduleChangeLog.objects
        .filter(callcenter=callcenter)
        .select_related("user")
        .first()
    )

    if not latest_change:
        return None

    user = latest_change.user

    return {
        "user": (
            user.get_full_name()
            or user.username
            if user
            else "Usuario eliminado"
        ),
        "reason": latest_change.reason,
        "created_at": latest_change.created_at,
    }


def _parse_time(value):
    return datetime.strptime(
        value,
        "%H:%M",
    ).time()


def _validate_overlaps(intervals):
    errors = []
    grouped = {}

    for interval in intervals:
        grouped.setdefault(
            interval["weekday"],
            [],
        ).append(interval)

    for weekday, day_intervals in grouped.items():
        ordered = sorted(
            day_intervals,
            key=lambda item: item["start_time"],
        )

        if not ordered:
            continue

        active_interval = ordered[0]

        for current in ordered[1:]:
            if (
                current["start_time"]
                < active_interval["end_time"]
            ):
                errors.append(
                    f"En {WEEKDAY_LABELS[weekday]}, "
                    f"el horario "
                    f"{current['start_time_raw']} - "
                    f"{current['end_time_raw']} "
                    "se cruza con "
                    f"{active_interval['start_time_raw']} - "
                    f"{active_interval['end_time_raw']}."
                )

            if (
                current["end_time"]
                > active_interval["end_time"]
            ):
                active_interval = current

    return errors


def _parse_schedule_post(post_data):
    weekdays = post_data.getlist("weekday")
    start_times = post_data.getlist("start_time")
    end_times = post_data.getlist("end_time")

    raw_rows = []
    intervals = []
    errors = []

    if not (
        len(weekdays)
        == len(start_times)
        == len(end_times)
    ):
        return (
            raw_rows,
            intervals,
            [
                (
                    "La información enviada está incompleta. "
                    "Recarga la página e intenta nuevamente."
                )
            ],
        )

    valid_weekdays = set(WEEKDAY_LABELS)

    for index, weekday in enumerate(weekdays):
        start_time_raw = start_times[index]
        end_time_raw = end_times[index]

        if weekday not in valid_weekdays:
            errors.append(
                "Se recibió un día no válido."
            )
            continue

        raw_rows.append(
            {
                "weekday": weekday,
                "start_time": start_time_raw,
                "end_time": end_time_raw,
            }
        )

        day_label = WEEKDAY_LABELS[weekday]

        if not start_time_raw or not end_time_raw:
            errors.append(
                f"Completa las dos horas de {day_label}."
            )
            continue

        try:
            start_time = _parse_time(start_time_raw)
            end_time = _parse_time(end_time_raw)
        except ValueError:
            errors.append(
                f"Hay una hora inválida en {day_label}."
            )
            continue

        if start_time >= end_time:
            errors.append(
                f"En {day_label}, la hora de inicio "
                "debe ser anterior a la hora final."
            )
            continue

        intervals.append(
            {
                "weekday": weekday,
                "start_time": start_time,
                "end_time": end_time,
                "start_time_raw": start_time_raw,
                "end_time_raw": end_time_raw,
            }
        )

    errors.extend(
        _validate_overlaps(intervals)
    )

    return raw_rows, intervals, errors


@login_required
def schedule_editor(request, codename):
    callcenter = get_callcenter_for_user(
        request.user,
        codename,
    )

    if request.method == "POST":
        change_reason = request.POST.get(
            "change_reason",
            "",
        ).strip()

        (
            raw_rows,
            intervals,
            errors,
        ) = _parse_schedule_post(
            request.POST,
        )

        if not change_reason:
            errors.append(
                "Escribe el motivo del cambio."
            )

        if errors:
            weekly_sections = _build_weekly_sections(
                raw_rows,
            )

            return render(
                request,
                "schedules/schedule_editor.html",
                {
                    "callcenter": callcenter,
                    "weekly_sections": weekly_sections,
                    "schedule_summary": (
                        _build_schedule_summary(
                            weekly_sections,
                        )
                    ),
                    "errors": errors,
                    "change_reason": change_reason,
                    "latest_change": _get_latest_change(
                        callcenter,
                    ),
                },
            )

        with transaction.atomic():
            ScheduleInterval.objects.filter(
                callcenter=callcenter,
            ).delete()

            ScheduleInterval.objects.bulk_create(
                [
                    ScheduleInterval(
                        callcenter=callcenter,
                        weekday=interval["weekday"],
                        start_time=interval["start_time"],
                        end_time=interval["end_time"],
                    )
                    for interval in intervals
                ]
            )

            ScheduleChangeLog.objects.create(
                callcenter=callcenter,
                user=request.user,
                reason=change_reason,
            )

        messages.success(
            request,
            "Horario guardado correctamente.",
        )

        return redirect(
            "schedules:editor",
            codename=callcenter.codename,
        )

    rows = _get_schedule_rows(
        callcenter,
    )

    weekly_sections = _build_weekly_sections(rows)

    return render(
        request,
        "schedules/schedule_editor.html",
        {
            "callcenter": callcenter,
            "weekly_sections": weekly_sections,
            "schedule_summary": (
                _build_schedule_summary(
                    weekly_sections,
                )
            ),
            "errors": [],
            "change_reason": "",
            "latest_change": _get_latest_change(
                callcenter,
            ),
        },
    )
