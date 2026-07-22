from django.db import migrations


CREATE_VIEW_SQL = """
CREATE VIEW schedules_asterisk_audio AS
SELECT
    callcenter.codename,
    CONCAT(
        'custom/callcenter_manager/',
        callcenter.closed_audio_file
    ) AS playback_file
FROM callcenters_callcenter AS callcenter
WHERE callcenter.is_active = TRUE;
"""


DROP_VIEW_SQL = """
DROP VIEW IF EXISTS schedules_asterisk_audio;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("callcenters", "0002_callcenter_closed_audio_file"),
        ("schedules", "0005_schedule_audit_snapshots"),
    ]

    operations = [
        migrations.RunSQL(
            sql=CREATE_VIEW_SQL,
            reverse_sql=DROP_VIEW_SQL,
        ),
    ]
