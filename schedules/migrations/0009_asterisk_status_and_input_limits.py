from django.db import migrations, models


FORWARD_SQL = """
CREATE OR REPLACE VIEW schedules_asterisk_schedule_legacy AS
SELECT
    CONCAT('/horario/', callcenter.codename, '/', schedule.weekday) AS astdb_key,
    STRING_AGG(
        TO_CHAR(schedule.start_time, 'HH24:MI') || '-' ||
        TO_CHAR(schedule.end_time, 'HH24:MI'),
        '|' ORDER BY schedule.start_time, schedule.end_time
    ) AS schedule_value
FROM schedules_scheduleinterval AS schedule
INNER JOIN callcenters_callcenter AS callcenter
    ON callcenter.id = schedule.callcenter_id
INNER JOIN clients_client AS client
    ON client.id = callcenter.client_id
WHERE callcenter.is_active = TRUE AND client.is_active = TRUE
GROUP BY callcenter.codename, schedule.weekday;

CREATE OR REPLACE VIEW schedules_asterisk_audio AS
SELECT
    callcenter.codename,
    CONCAT('custom/callcenter_manager/', callcenter.closed_audio_file) AS playback_file
FROM callcenters_callcenter AS callcenter
INNER JOIN clients_client AS client
    ON client.id = callcenter.client_id
WHERE callcenter.is_active = TRUE AND client.is_active = TRUE;

CREATE VIEW schedules_asterisk_callcenter_status AS
SELECT
    callcenter.codename,
    COALESCE(valid_timezone.name, 'UTC') AS timezone,
    (callcenter.is_active AND client.is_active) AS is_enabled,
    (
        callcenter.is_active
        AND client.is_active
        AND EXISTS (
            SELECT 1
            FROM schedules_scheduleinterval AS schedule
            WHERE schedule.callcenter_id = callcenter.id
              AND schedule.weekday = CASE EXTRACT(ISODOW FROM clock.local_now)
                    WHEN 1 THEN 'Mon'
                    WHEN 2 THEN 'Tue'
                    WHEN 3 THEN 'Wed'
                    WHEN 4 THEN 'Thu'
                    WHEN 5 THEN 'Fri'
                    WHEN 6 THEN 'Sat'
                    WHEN 7 THEN 'Sun'
                  END
              AND clock.local_now::time >= schedule.start_time
              AND clock.local_now::time < schedule.end_time
        )
    ) AS is_open,
    CONCAT('custom/callcenter_manager/', callcenter.closed_audio_file) AS playback_file
FROM callcenters_callcenter AS callcenter
INNER JOIN clients_client AS client
    ON client.id = callcenter.client_id
LEFT JOIN LATERAL (
    SELECT name
    FROM pg_timezone_names
    WHERE name = callcenter.timezone
    LIMIT 1
) AS valid_timezone ON TRUE
CROSS JOIN LATERAL (
    SELECT CURRENT_TIMESTAMP AT TIME ZONE COALESCE(valid_timezone.name, 'UTC') AS local_now
) AS clock;
"""


REVERSE_SQL = """
DROP VIEW IF EXISTS schedules_asterisk_callcenter_status;

CREATE OR REPLACE VIEW schedules_asterisk_schedule_legacy AS
SELECT
    CONCAT('/horario/', callcenter.codename, '/', schedule.weekday) AS astdb_key,
    STRING_AGG(
        TO_CHAR(schedule.start_time, 'HH24:MI') || '-' ||
        TO_CHAR(schedule.end_time, 'HH24:MI'),
        '|' ORDER BY schedule.start_time, schedule.end_time
    ) AS schedule_value
FROM schedules_scheduleinterval AS schedule
INNER JOIN callcenters_callcenter AS callcenter
    ON callcenter.id = schedule.callcenter_id
WHERE callcenter.is_active = TRUE
GROUP BY callcenter.codename, schedule.weekday;

CREATE OR REPLACE VIEW schedules_asterisk_audio AS
SELECT
    callcenter.codename,
    CONCAT('custom/callcenter_manager/', callcenter.closed_audio_file) AS playback_file
FROM callcenters_callcenter AS callcenter
WHERE callcenter.is_active = TRUE;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("callcenters", "0006_unique_callcenter_name_per_client_ci"),
        ("schedules", "0008_alter_schedulechangelog_audio_file"),
    ]

    operations = [
        migrations.AlterField(
            model_name="schedulechangelog",
            name="reason",
            field=models.CharField(max_length=500),
        ),
        migrations.AlterField(
            model_name="schedulechangelog",
            name="user_agent",
            field=models.CharField(blank=True, max_length=512),
        ),
        migrations.RunSQL(sql=FORWARD_SQL, reverse_sql=REVERSE_SQL),
    ]
