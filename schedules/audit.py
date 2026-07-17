from config.request_utils import get_client_ip

from .models import ScheduleChangeLog, ScheduleInterval, Weekday


WEEKDAY_LABELS = {
    weekday: label
    for weekday, label in Weekday.choices
}


def _time_to_string(value):
    return value.strftime("%H:%M")


def _format_time_label(value):
    try:
        hour, minute = value.split(":")
        hour = int(hour)
    except (AttributeError, TypeError, ValueError):
        return value

    display_hour = hour % 12 or 12
    period = "a. m." if hour < 12 else "p. m."

    return f"{display_hour:02d}:{minute} {period}"


def _format_intervals(intervals):
    if not intervals:
        return "Cerrado"

    return ", ".join(
        (
            f"{_format_time_label(interval.get('start'))} - "
            f"{_format_time_label(interval.get('end'))}"
        )
        for interval in intervals
    )


def get_schedule_change_summary(before_snapshot, after_snapshot):
    before_days = (before_snapshot or {}).get("days") or {}
    after_days = (after_snapshot or {}).get("days") or {}
    summaries = []

    for weekday, label in Weekday.choices:
        before_intervals = before_days.get(weekday, [])
        after_intervals = after_days.get(weekday, [])

        if before_intervals == after_intervals:
            continue

        summaries.append(
            {
                "day": label,
                "before": _format_intervals(before_intervals),
                "after": _format_intervals(after_intervals),
            }
        )

    if not summaries:
        return "Sin cambios de horario"

    first_change = summaries[0]
    summary = (
        f"{first_change['day']}: "
        f"{first_change['before']} → {first_change['after']}"
    )

    extra_count = len(summaries) - 1

    if extra_count:
        summary = f"{summary} · +{extra_count} día(s)"

    return summary


def build_schedule_snapshot(callcenter):
    days = {
        weekday: []
        for weekday, _label in Weekday.choices
    }

    intervals = (
        ScheduleInterval.objects
        .filter(callcenter=callcenter)
        .order_by(
            "weekday",
            "start_time",
            "end_time",
        )
    )

    for interval in intervals:
        days[interval.weekday].append(
            {
                "start": _time_to_string(
                    interval.start_time,
                ),
                "end": _time_to_string(
                    interval.end_time,
                ),
            }
        )

    return {
        "version": 1,
        "codename": callcenter.codename,
        "timezone": callcenter.timezone,
        "days": days,
    }


def get_user_agent(request):
    return request.META.get("HTTP_USER_AGENT", "")


def create_schedule_change_log(
    *,
    callcenter,
    user,
    reason,
    before_snapshot,
    after_snapshot,
    audio_file="",
    audio_label="",
    request=None,
):
    ip_address = None
    user_agent = ""

    if request is not None:
        ip_address = get_client_ip(request)
        user_agent = get_user_agent(request)

    return ScheduleChangeLog.objects.create(
        callcenter=callcenter,
        user=user if user.is_authenticated else None,
        reason=reason,
        before_snapshot=before_snapshot,
        after_snapshot=after_snapshot,
        audio_file=audio_file,
        audio_label=audio_label,
        ip_address=ip_address,
        user_agent=user_agent,
    )


def get_snapshot_days(snapshot):
    days = snapshot.get("days") or {}

    return [
        {
            "value": weekday,
            "label": label,
            "intervals": days.get(weekday, []),
        }
        for weekday, label in Weekday.choices
    ]
