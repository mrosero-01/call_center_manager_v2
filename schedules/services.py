from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.utils import timezone

from callcenters.models import CallCenter


WEEKDAYS = (
    "Mon",
    "Tue",
    "Wed",
    "Thu",
    "Fri",
    "Sat",
    "Sun",
)


def is_callcenter_open(
    codename: str,
    at: datetime | None = None,
) -> bool:
    callcenter = CallCenter.objects.get(codename=codename)

    if not callcenter.is_active:
        return False

    try:
        callcenter_timezone = ZoneInfo(callcenter.timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(
            f"Zona horaria inválida: {callcenter.timezone}"
        ) from exc

    current_datetime = at or timezone.now()

    if timezone.is_naive(current_datetime):
        raise ValueError(
            "La fecha recibida debe incluir zona horaria."
        )

    local_datetime = current_datetime.astimezone(
        callcenter_timezone
    )

    weekday = WEEKDAYS[local_datetime.weekday()]

    current_time = local_datetime.time().replace(
        second=0,
        microsecond=0,
        tzinfo=None,
    )

    return callcenter.schedule_intervals.filter(
        weekday=weekday,
        start_time__lte=current_time,
        end_time__gte=current_time,
    ).exists()