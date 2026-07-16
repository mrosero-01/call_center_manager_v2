from django.db import migrations, models


AUDIO_LABELS = {
    "schedule_changed": "Horario modificado",
    "temporarily_unavailable": "Atención no disponible",
    "special_day": "Festivo o evento especial",
}


def populate_audio_labels(apps, schema_editor):
    ScheduleChangeLog = apps.get_model(
        "schedules",
        "ScheduleChangeLog",
    )

    for change_log in ScheduleChangeLog.objects.all():
        change_log.audio_label = AUDIO_LABELS.get(
            change_log.audio_file,
            "",
        )
        change_log.save(
            update_fields=[
                "audio_label",
            ],
        )


class Migration(migrations.Migration):

    dependencies = [
        ("schedules", "0004_schedulechangelog_audio_key"),
    ]

    operations = [
        migrations.RenameField(
            model_name="schedulechangelog",
            old_name="audio_key",
            new_name="audio_file",
        ),
        migrations.AddField(
            model_name="schedulechangelog",
            name="before_snapshot",
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name="schedulechangelog",
            name="after_snapshot",
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name="schedulechangelog",
            name="audio_file",
            field=models.CharField(
                blank=True,
                choices=[
                    ("schedule_changed", "Horario modificado"),
                    (
                        "temporarily_unavailable",
                        "Atención no disponible",
                    ),
                    (
                        "special_day",
                        "Festivo o evento especial",
                    ),
                ],
                max_length=60,
            ),
        ),
        migrations.AddField(
            model_name="schedulechangelog",
            name="audio_label",
            field=models.CharField(
                blank=True,
                max_length=120,
            ),
        ),
        migrations.AddField(
            model_name="schedulechangelog",
            name="ip_address",
            field=models.GenericIPAddressField(
                blank=True,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="schedulechangelog",
            name="user_agent",
            field=models.TextField(blank=True),
        ),
        migrations.RunPython(
            populate_audio_labels,
            migrations.RunPython.noop,
        ),
        migrations.AddIndex(
            model_name="schedulechangelog",
            index=models.Index(
                fields=[
                    "-created_at",
                ],
                name="schedules_s_created_dfc31f_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="schedulechangelog",
            index=models.Index(
                fields=[
                    "callcenter",
                    "-created_at",
                ],
                name="schedules_s_callcen_b8096c_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="schedulechangelog",
            index=models.Index(
                fields=[
                    "user",
                    "-created_at",
                ],
                name="schedules_s_user_id_bd6d79_idx",
            ),
        ),
    ]
