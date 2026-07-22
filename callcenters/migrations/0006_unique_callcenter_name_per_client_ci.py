from django.db import migrations, models
from django.db.models.functions import Lower


class Migration(migrations.Migration):
    dependencies = [
        ("callcenters", "0005_callcenter_schedule_version"),
        ("clients", "0002_unique_client_name_ci"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="callcenter",
            constraint=models.UniqueConstraint(
                models.F("client"),
                Lower("name"),
                name="unique_callcenter_name_per_client_ci",
            ),
        ),
    ]
