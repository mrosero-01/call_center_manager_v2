from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("callcenters", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="callcenter",
            name="closed_audio_file",
            field=models.CharField(
                choices=[
                    (
                        "schedule_changed",
                        "Horario modificado",
                    ),
                    (
                        "temporarily_unavailable",
                        "Atención no disponible",
                    ),
                    (
                        "special_day",
                        "Festivo o evento especial",
                    ),
                ],
                default="schedule_changed",
                max_length=60,
            ),
        ),
    ]
