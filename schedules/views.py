from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import transaction
from django.shortcuts import redirect, render
from django.templatetags.static import static
from django.urls import reverse

from callcenters.selectors import get_callcenter_for_user

from .models import (
    ScheduleAudio,
    ScheduleChangeLog,
    ScheduleInterval,
    Weekday,
)


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

VALID_WEEKDAYS = set(WEEKDAY_LABELS)
SAVE_RATE_LIMIT = 10
SAVE_RATE_WINDOW_SECONDS = 60

SCHEDULE_AUDIO_OPTIONS = [
    {
        "key": ScheduleAudio.SCHEDULE_CHANGED,
        "label": ScheduleAudio.SCHEDULE_CHANGED.label,
        "title": "Audio 1",
        "icon": "🔊",
        "description": (
            "Informa que el horario de atención cambió "
            "temporalmente."
        ),
        "preview_url": static(
            "audio/schedules/schedule_changed.mp3",
        ),
    },
    {
        "key": ScheduleAudio.TEMPORARILY_UNAVAILABLE,
        "label": ScheduleAudio.TEMPORARILY_UNAVAILABLE.label,
        "title": "Audio 2",
        "icon": "🔇",
        "description": (
            "Indica que la atención no está disponible "
            "en este momento."
        ),
        "preview_url": static(
            "audio/schedules/temporarily_unavailable.mp3",
        ),
    },
    {
        "key": ScheduleAudio.SPECIAL_DAY,
        "label": ScheduleAudio.SPECIAL_DAY.label,
        "title": "Audio 3",
        "icon": "📅",
        "description": (
            "Aviso para fechas especiales o eventos "
            "operativos."
        ),
        "preview_url": static(
            "audio/schedules/special_day.mp3",
        ),
    },
]

SCHEDULE_AUDIO_LABELS = {
    option["key"]: option["label"]
    for option in SCHEDULE_AUDIO_OPTIONS
}


def _get_selected_weekday(value):
    if value in VALID_WEEKDAYS:
        return value

    return Weekday.MONDAY


def _get_audio_key(value):
    if value in SCHEDULE_AUDIO_LABELS:
        return value

    return ""


def _schedule_save_rate_key(user, callcenter):
    return (
        "schedule-save-rate:"
        f"{user.pk}:{callcenter.pk}"
    )


def _is_schedule_save_rate_limited(user, callcenter):
    cache_key = _schedule_save_rate_key(
        user,
        callcenter,
    )
    attempts = cache.get(
        cache_key,
        0,
    )

    if attempts >= SAVE_RATE_LIMIT:
        return True

    if cache.add(
        cache_key,
        1,
        SAVE_RATE_WINDOW_SECONDS,
    ):
        return False

    try:
        cache.incr(cache_key)
    except ValueError:
        cache.set(
            cache_key,
            1,
            SAVE_RATE_WINDOW_SECONDS,
        )

    return False


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


def _format_change_log(change_log):
    user = change_log.user

    return {
        "user": (
            user.get_full_name()
            or user.username
            if user
            else "Usuario eliminado"
        ),
        "reason": change_log.reason,
        "audio_label": SCHEDULE_AUDIO_LABELS.get(
            change_log.audio_key,
            change_log.audio_key,
        ),
        "created_at": change_log.created_at,
    }


def _get_recent_changes(callcenter):
    return [
        _format_change_log(change_log)
        for change_log in (
            ScheduleChangeLog.objects
            .filter(callcenter=callcenter)
            .select_related("user")[:5]
        )
    ]


def _get_change_context(callcenter):
    recent_changes = _get_recent_changes(callcenter)

    return {
        "latest_change": (
            recent_changes[0]
            if recent_changes
            else None
        ),
        "recent_changes": recent_changes,
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
                f"En {day_label}, la hora de cierre "
                "debe ser posterior a la hora de inicio."
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
        selected_weekday = _get_selected_weekday(
            request.POST.get("selected_weekday"),
        )
        change_reason = request.POST.get(
            "change_reason",
            "",
        ).strip()
        audio_key = _get_audio_key(
            request.POST.get("audio_key"),
        )

        (
            raw_rows,
            intervals,
            errors,
        ) = _parse_schedule_post(
            request.POST,
        )

        if _is_schedule_save_rate_limited(
            request.user,
            callcenter,
        ):
            errors.append(
                (
                    "Se hicieron demasiados intentos de guardado. "
                    "Espera un momento e inténtalo de nuevo."
                )
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
                    "audio_options": SCHEDULE_AUDIO_OPTIONS,
                    "selected_audio_key": audio_key,
                    **_get_change_context(callcenter),
                    "selected_weekday": selected_weekday,
                    "save_feedback": "",
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

            change_log_data = {
                "callcenter": callcenter,
                "user": request.user,
                "reason": change_reason,
            }

            if audio_key:
                change_log_data["audio_key"] = audio_key

            ScheduleChangeLog.objects.create(
                **change_log_data,
            )

        editor_url = reverse(
            "schedules:editor",
            kwargs={
                "codename": callcenter.codename,
            },
        )

        return redirect(
            f"{editor_url}?day={selected_weekday}&saved=1",
        )

    rows = _get_schedule_rows(
        callcenter,
    )

    weekly_sections = _build_weekly_sections(rows)
    selected_weekday = _get_selected_weekday(
        request.GET.get("day"),
    )
    save_feedback = ""

    if request.GET.get("saved") == "1":
        save_feedback = "Todos los cambios guardados"

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
            "audio_options": SCHEDULE_AUDIO_OPTIONS,
            "selected_audio_key": "",
            **_get_change_context(callcenter),
            "selected_weekday": selected_weekday,
            "save_feedback": save_feedback,
        },
    )
