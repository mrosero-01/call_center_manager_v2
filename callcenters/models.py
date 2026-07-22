from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.functions import Lower


codename_validator = RegexValidator(
    regex=r"^[a-z0-9]+(?:_[a-z0-9]+)*$",
    message=(
        "El codename solo puede contener letras minúsculas, "
        "números y guiones bajos."
    ),
)


CLOSED_AUDIO_CHOICES = (
    (
        "falla_tecnica",
        "Falla técnica",
    ),
    (
        "reentrenamiento_personal",
        "Reentrenamiento de personal",
    ),
)


class CallCenter(models.Model):
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.PROTECT,
        related_name="callcenters",
    )

    name = models.CharField(max_length=100)

    codename = models.CharField(
        max_length=100,
        unique=True,
        validators=[codename_validator],
    )

    timezone = models.CharField(
        max_length=64,
        default="America/Bogota",
    )

    is_active = models.BooleanField(default=True)

    closed_audio_file = models.CharField(
        max_length=60,
        choices=CLOSED_AUDIO_CHOICES,
        default="falla_tecnica",
    )

    schedule_version = models.PositiveBigIntegerField(
        default=1,
        editable=False,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                models.F("client"),
                Lower("name"),
                name="unique_callcenter_name_per_client_ci",
            ),
        ]

    def clean(self):
        super().clean()

        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError as exc:
            raise ValidationError(
                {"timezone": "Escribe una zona horaria IANA válida."}
            ) from exc

    def __str__(self):
        return f"{self.client.name} - {self.name} ({self.codename})"
