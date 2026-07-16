from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Weekday(models.TextChoices):
    MONDAY = "Mon", "Lunes"
    TUESDAY = "Tue", "Martes"
    WEDNESDAY = "Wed", "Miércoles"
    THURSDAY = "Thu", "Jueves"
    FRIDAY = "Fri", "Viernes"
    SATURDAY = "Sat", "Sábado"
    SUNDAY = "Sun", "Domingo"


class ScheduleAudio(models.TextChoices):
    SCHEDULE_CHANGED = (
        "schedule_changed",
        "Horario modificado",
    )
    TEMPORARILY_UNAVAILABLE = (
        "temporarily_unavailable",
        "Atención no disponible",
    )
    SPECIAL_DAY = (
        "special_day",
        "Festivo o evento especial",
    )


class ScheduleInterval(models.Model):
    callcenter = models.ForeignKey(
        "callcenters.CallCenter",
        on_delete=models.PROTECT,
        related_name="schedule_intervals",
    )

    weekday = models.CharField(
        max_length=3,
        choices=Weekday.choices,
    )

    start_time = models.TimeField()

    end_time = models.TimeField()

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(start_time__lt=F("end_time")),
                name="schedule_start_before_end",
            ),
            models.UniqueConstraint(
                fields=[
                    "callcenter",
                    "weekday",
                    "start_time",
                    "end_time",
                ],
                name="unique_schedule_interval",
            ),
        ]

    def __str__(self):
        return (
            f"{self.callcenter.codename} - "
            f"{self.weekday} "
            f"{self.start_time:%H:%M}-{self.end_time:%H:%M}"
        )


class ScheduleChangeLog(models.Model):
    callcenter = models.ForeignKey(
        "callcenters.CallCenter",
        on_delete=models.PROTECT,
        related_name="schedule_change_logs",
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="schedule_change_logs",
        null=True,
        blank=True,
    )

    reason = models.TextField()

    before_snapshot = models.JSONField(
        default=dict,
    )

    after_snapshot = models.JSONField(
        default=dict,
    )

    audio_file = models.CharField(
        max_length=60,
        choices=ScheduleAudio.choices,
        blank=True,
    )

    audio_label = models.CharField(
        max_length=120,
        blank=True,
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = (
            "-created_at",
        )
        indexes = [
            models.Index(
                fields=[
                    "-created_at",
                ],
            ),
            models.Index(
                fields=[
                    "callcenter",
                    "-created_at",
                ],
            ),
            models.Index(
                fields=[
                    "user",
                    "-created_at",
                ],
            ),
        ]

    def __str__(self):
        return (
            f"{self.callcenter.codename} - "
            f"{self.created_at:%Y-%m-%d %H:%M}"
        )
