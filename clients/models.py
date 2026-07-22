from django.db import models
from django.db.models.functions import Lower

# Create your models here.
class Client(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="unique_client_name_case_insensitive",
            ),
        ]

    def __str__(self):
        return self.name
