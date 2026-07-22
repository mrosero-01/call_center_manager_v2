from django.db import migrations, models


AUDIO_VALUE_MAP = {
    "technical_failure": "falla_tecnica",
    "staff_retraining": "reentrenamiento_personal",
}


def migrate_audio_values(apps, schema_editor):
    CallCenter = apps.get_model(
        "callcenters",
        "CallCenter",
    )

    for old_value, new_value in AUDIO_VALUE_MAP.items():
        CallCenter.objects.filter(
            closed_audio_file=old_value,
        ).update(
            closed_audio_file=new_value,
        )


class Migration(migrations.Migration):

    dependencies = [
        ("callcenters", "0003_alter_callcenter_closed_audio_file"),
    ]

    operations = [
        migrations.RunPython(
            migrate_audio_values,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="callcenter",
            name="closed_audio_file",
            field=models.CharField(
                choices=[
                    (
                        "falla_tecnica",
                        "Falla técnica",
                    ),
                    (
                        "reentrenamiento_personal",
                        "Reentrenamiento de personal",
                    ),
                ],
                default="falla_tecnica",
                max_length=60,
            ),
        ),
    ]
