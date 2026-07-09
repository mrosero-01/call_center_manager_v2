from django.db import models
from django.db.models import F, Q
# Create your models here.

class Weekday(models.TextChoices):
    MONDAY = "Mon", "Lunes"
    TUESDAY = "Tue", "Martes"
    WEDNESDAY = "Wed", "Miércoles"
    THURSDAY = "Thu", "Jueves"
    FRIDAY = "Fri", "Viernes"
    SATURDAY = "Sat", "Sábado"
    SUNDAY = "Sun", "Domingo"


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