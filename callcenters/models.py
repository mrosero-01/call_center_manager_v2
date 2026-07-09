from django.core.validators import RegexValidator
from django.db import models


codename_validator = RegexValidator(
    regex=r"^[a-z0-9]+(?:_[a-z0-9]+)*$",
    message=(
        "El codename solo puede contener letras minúsculas, "
        "números y guiones bajos."
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

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client.name} - {self.name} ({self.codename})"