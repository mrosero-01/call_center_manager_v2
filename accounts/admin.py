from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "Call Center Manager",
            {
                "fields": (
                    "client",
                ),
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Call Center Manager",
            {
                "fields": (
                    "client",
                ),
            },
        ),
    )

    list_display = (
        "username",
        "email",
        "client",
        "is_staff",
        "is_superuser",
        "is_active",
    )

    list_filter = (
        "is_superuser",
        "is_staff",
        "is_active",
        "client",
    )