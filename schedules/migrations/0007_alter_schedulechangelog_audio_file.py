from django.db import migrations, models


AUDIO_VALUE_MAP = {
    "schedule_changed": (
        "technical_failure",
        "Falla técnica",
    ),
    "temporarily_unavailable": (
        "technical_failure",
        "Falla técnica",
    ),
    "special_day": (
        "staff_retraining",
        "Reentrenamiento de personal",
    ),
}


def migrate_audio_values(apps, schema_editor):
    ScheduleChangeLog = apps.get_model(
        "schedules",
        "ScheduleChangeLog",
    )

    for change_log in ScheduleChangeLog.objects.all().iterator():
        replacement = AUDIO_VALUE_MAP.get(
            change_log.audio_file,
        )
        update_fields = []

        if replacement:
            change_log.audio_file = replacement[0]
            change_log.audio_label = replacement[1]
            update_fields.extend(
                [
                    "audio_file",
                    "audio_label",
                ]
            )

        for field_name in (
            "before_snapshot",
            "after_snapshot",
        ):
            snapshot = getattr(change_log, field_name) or {}
            snapshot_audio = snapshot.get("closed_audio_file")
            snapshot_replacement = AUDIO_VALUE_MAP.get(snapshot_audio)

            if snapshot_replacement:
                snapshot["closed_audio_file"] = snapshot_replacement[0]
                setattr(change_log, field_name, snapshot)
                update_fields.append(field_name)

        if update_fields:
            change_log.save(
                update_fields=list(dict.fromkeys(update_fields)),
            )


class Migration(migrations.Migration):

    dependencies = [
        ("callcenters", "0003_alter_callcenter_closed_audio_file"),
        ("schedules", "0006_add_asterisk_audio_view"),
    ]

    operations = [
        migrations.RunPython(
            migrate_audio_values,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="schedulechangelog",
            name="audio_file",
            field=models.CharField(
                blank=True,
                choices=[
                    (
                        "technical_failure",
                        "Falla técnica",
                    ),
                    (
                        "staff_retraining",
                        "Reentrenamiento de personal",
                    ),
                ],
                max_length=60,
            ),
        ),
    ]
