from django.contrib import admin

from .models import CallCenter


@admin.register(CallCenter)
class CallCenterAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "codename",
        "client",
        "timezone",
        "is_active",
    )

    list_filter = (
        "is_active",
        "client",
        "timezone",
    )

    search_fields = (
        "name",
        "codename",
        "client__name",
    )