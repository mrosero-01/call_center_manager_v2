from django.db import migrations, models
from django.db.models.functions import Lower


class Migration(migrations.Migration):
    dependencies = [
        ("clients", "0001_initial"),
    ]

    operations = [
        migrations.AddConstraint(
            model_name="client",
            constraint=models.UniqueConstraint(
                Lower("name"),
                name="unique_client_name_case_insensitive",
            ),
        ),
    ]
