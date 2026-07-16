from .models import ScheduleChangeLog, ScheduleInterval, Weekday


def _time_to_string(value):
    return value.strftime("%H:%M")


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


def get_client_ip(request):
    return request.META.get("REMOTE_ADDR") or None


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
