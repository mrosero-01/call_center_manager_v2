from django.contrib import admin

from .models import ScheduleChangeLog, ScheduleInterval


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


@admin.register(ScheduleChangeLog)
class ScheduleChangeLogAdmin(admin.ModelAdmin):
    list_display = (
        "callcenter",
        "user",
        "created_at",
    )

    list_filter = (
        "callcenter",
        "created_at",
    )

    search_fields = (
        "callcenter__name",
        "callcenter__codename",
        "user__username",
        "reason",
    )

    readonly_fields = (
        "callcenter",
        "user",
        "reason",
        "created_at",
    )

    ordering = (
        "-created_at",
    )
