from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import Q


class User(AbstractUser):
    client = models.ForeignKey(
        "clients.Client",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(is_superuser=True)
                    | Q(client__isnull=False)
                ),
                name="user_superuser_or_has_client",
            ),
        ]