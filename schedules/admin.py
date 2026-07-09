from django.contrib import admin

from .models import ScheduleInterval


@admin.register(ScheduleInterval)
class ScheduleIntervalAdmin(admin.ModelAdmin):
    list_display = (
        "callcenter",
        "weekday",
        "start_time",
        "end_time",
    )

    list_filter = (
        "weekday",
        "callcenter",
    )

    search_fields = (
        "callcenter__name",
        "callcenter__codename",
    )

    ordering = (
        "callcenter",
        "weekday",
        "start_time",
    )