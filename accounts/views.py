from django.contrib.auth.decorators import login_required
from django.contrib.auth import views as auth_views
from django.core.cache import cache
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

LOGIN_RATE_LIMIT = 5
LOGIN_RATE_WINDOW_SECONDS = 300


def _get_client_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR", "unknown")


def _login_rate_key(request):
    return f"login-rate:{_get_client_ip(request)}"


class RateLimitedLoginView(auth_views.LoginView):
    template_name = "accounts/login.html"

    def dispatch(self, request, *args, **kwargs):
        if request.method == "POST":
            attempts = cache.get(
                _login_rate_key(request),
                0,
            )

            if attempts >= LOGIN_RATE_LIMIT:
                form = self.get_form()
                form.add_error(
                    None,
                    (
                        "Demasiados intentos de inicio de sesión. "
                        "Espera unos minutos e inténtalo de nuevo."
                    ),
                )

                return self.form_invalid(form)

        return super().dispatch(
            request,
            *args,
            **kwargs,
        )

    def form_invalid(self, form):
        cache_key = _login_rate_key(self.request)

        if cache.add(
            cache_key,
            1,
            LOGIN_RATE_WINDOW_SECONDS,
        ):
            return super().form_invalid(form)

        try:
            cache.incr(cache_key)
        except ValueError:
            cache.set(
                cache_key,
                1,
                LOGIN_RATE_WINDOW_SECONDS,
            )

        return super().form_invalid(form)

    def form_valid(self, form):
        cache.delete(
            _login_rate_key(self.request),
        )

        return super().form_valid(form)


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
