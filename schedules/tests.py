from datetime import datetime
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from django.test import TestCase
from django.urls import reverse

from callcenters.models import CallCenter
from clients.models import Client

from .models import (
    ScheduleAudio,
    ScheduleChangeLog,
    ScheduleInterval,
    Weekday,
)


class ScheduleEditorTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client_account = Client.objects.create(
            name="Cliente de prueba",
        )
        self.user = get_user_model().objects.create_user(
            username="agent",
            password="password",
            client=self.client_account,
        )
        self.callcenter = CallCenter.objects.create(
            client=self.client_account,
            name="Campaña prueba",
            codename="campana_prueba",
        )
        self.url = reverse(
            "schedules:editor",
            kwargs={
                "codename": self.callcenter.codename,
            },
        )
        self.client.force_login(self.user)

    def post_schedule(
        self,
        weekdays,
        starts,
        ends,
        reason,
        audio_file=ScheduleAudio.TECHNICAL_FAILURE,
        change_type="apertura",
        schedule_version=None,
    ):
        if schedule_version is None:
            self.callcenter.refresh_from_db()
            schedule_version = self.callcenter.schedule_version

        return self.client.post(
            self.url,
            {
                "weekday": weekdays,
                "start_time": starts,
                "end_time": ends,
                "change_reason": reason,
                "audio_file": audio_file,
                "change_type": change_type,
                "schedule_version": schedule_version,
            },
            REMOTE_ADDR="127.0.0.10",
            HTTP_USER_AGENT="Schedule test browser",
        )

    def test_requires_change_reason(self):
        response = self.post_schedule(
            [Weekday.MONDAY],
            ["08:00"],
            ["12:00"],
            "",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Escribe el motivo del cambio.",
        )
        self.assertEqual(
            ScheduleInterval.objects.count(),
            0,
        )
    def test_requires_audio_reference(self):
        response = self.post_schedule(
            [],
            [],
            [],
            "Ajuste operativo",
            audio_file="",
            change_type="cierre",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Selecciona el mensaje de audio que escuchará el cliente.",
        )
        self.assertEqual(
            ScheduleInterval.objects.count(),
            0,
        )
        self.assertEqual(
            ScheduleChangeLog.objects.count(),
            0,
        )

    def test_requires_change_type(self):
        response = self.post_schedule(
            [Weekday.MONDAY],
            ["08:00"],
            ["12:00"],
            "Ajuste operativo",
            change_type="",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Selecciona si el cambio es de apertura o cierre.",
        )
        self.assertEqual(ScheduleInterval.objects.count(), 0)

    def test_audio_radios_do_not_use_hidden_native_required_validation(self):
        response = self.client.get(self.url)

        self.assertContains(
            response,
            'name="audio_file"',
            count=2,
        )
        self.assertContains(response, 'value="falla_tecnica"')
        self.assertContains(response, 'value="reentrenamiento_personal"')
        self.assertNotContains(
            response,
            'value="falla_tecnica"\n                                required',
        )

    def test_rejects_more_than_two_intervals_per_day(self):
        response = self.post_schedule(
            [
                Weekday.MONDAY,
                Weekday.MONDAY,
                Weekday.MONDAY,
            ],
            [
                "08:00",
                "10:00",
                "12:00",
            ],
            [
                "09:00",
                "11:00",
                "13:00",
            ],
            "Ajuste operativo",
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertContains(
            response,
            "Lunes puede tener máximo 2 horarios.",
        )
        self.assertEqual(
            ScheduleInterval.objects.filter(
                callcenter=self.callcenter,
                weekday=Weekday.MONDAY,
            ).count(),
            0,
        )

    def test_rejects_end_time_before_or_equal_start_time(self):
        response = self.post_schedule(
            [Weekday.TUESDAY],
            ["12:00"],
            ["12:00"],
            "Ajuste operativo",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "debe ser posterior a la hora de inicio",
        )
        self.assertEqual(
            ScheduleInterval.objects.count(),
            0,
        )

    def test_rejects_nested_overlapping_intervals(self):
        response = self.post_schedule(
            [
                Weekday.WEDNESDAY,
                Weekday.WEDNESDAY,
            ],
            [
                "08:00",
                "09:00",
            ],
            [
                "18:00",
                "10:00",
            ],
            "Ajuste operativo",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "se cruza con",
        )
        self.assertEqual(
            ScheduleInterval.objects.count(),
            0,
        )

    def test_user_cannot_edit_callcenter_from_other_client(self):
        other_client = Client.objects.create(
            name="Otro cliente",
        )
        other_callcenter = CallCenter.objects.create(
            client=other_client,
            name="Campaña ajena",
            codename="campana_ajena",
        )
        url = reverse(
            "schedules:editor",
            kwargs={
                "codename": other_callcenter.codename,
            },
        )

        response = self.client.get(url)

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_user_cannot_edit_inactive_callcenter(self):
        self.callcenter.is_active = False
        self.callcenter.save(update_fields=["is_active"])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)

    def test_user_cannot_edit_callcenter_when_client_is_inactive(self):
        self.client_account.is_active = False
        self.client_account.save(update_fields=["is_active"])

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 404)

    def test_schedule_save_rate_limit(self):
        for index in range(10):
            response = self.post_schedule(
                [Weekday.MONDAY],
                ["08:00"],
                [f"12:{index:02d}"],
                f"Ajuste operativo {index}",
            )

            self.assertEqual(
                response.status_code,
                302,
            )

        response = self.post_schedule(
            [Weekday.MONDAY],
            ["08:00"],
            ["12:00"],
            "Ajuste operativo bloqueado",
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertContains(
            response,
            "demasiados intentos de guardado",
        )
        self.assertEqual(
            ScheduleChangeLog.objects.count(),
            10,
        )

    def test_rejects_stale_schedule_version(self):
        stale_version = self.callcenter.schedule_version
        first_response = self.post_schedule(
            [Weekday.MONDAY],
            ["08:00"],
            ["12:00"],
            "Primer cambio",
            schedule_version=stale_version,
        )
        self.assertEqual(first_response.status_code, 302)

        response = self.post_schedule(
            [Weekday.TUESDAY],
            ["09:00"],
            ["13:00"],
            "Cambio desde una pantalla desactualizada",
            schedule_version=stale_version,
        )

        self.assertEqual(response.status_code, 409)
        self.assertContains(
            response,
            "modificado por otro usuario",
            status_code=409,
        )
        self.assertFalse(
            ScheduleInterval.objects.filter(
                weekday=Weekday.TUESDAY,
            ).exists()
        )

    def test_rejects_change_reason_over_500_characters(self):
        response = self.post_schedule(
            [Weekday.MONDAY],
            ["08:00"],
            ["12:00"],
            "x" * 501,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "no puede superar los 500")
        self.assertEqual(ScheduleChangeLog.objects.count(), 0)

    def test_rejects_overlapping_intervals(self):
        response = self.post_schedule(
            [
                Weekday.WEDNESDAY,
                Weekday.WEDNESDAY,
            ],
            [
                "08:00",
                "11:00",
            ],
            [
                "12:00",
                "14:00",
            ],
            "Ajuste operativo",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "se cruza con",
        )
        self.assertEqual(
            ScheduleInterval.objects.count(),
            0,
        )

    def test_saves_schedule_and_logs_change_reason(self):
        response = self.post_schedule(
            [
                Weekday.THURSDAY,
                Weekday.THURSDAY,
            ],
            [
                "08:00",
                "14:00",
            ],
            [
                "12:00",
                "18:00",
            ],
            "Cambio por capacitación",
            audio_file=ScheduleAudio.STAFF_RETRAINING,
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            ScheduleInterval.objects.filter(
                callcenter=self.callcenter,
            ).count(),
            2,
        )

        change_log = ScheduleChangeLog.objects.get(
            callcenter=self.callcenter,
        )

        self.assertEqual(
            change_log.user,
            self.user,
        )
        self.assertEqual(
            change_log.reason,
            "Cambio por capacitación",
        )
        self.assertEqual(
            change_log.audio_file,
            ScheduleAudio.TECHNICAL_FAILURE,
        )
        self.assertEqual(
            change_log.audio_label,
            ScheduleAudio.TECHNICAL_FAILURE.label,
        )
        self.callcenter.refresh_from_db()
        self.assertEqual(
            self.callcenter.closed_audio_file,
            ScheduleAudio.TECHNICAL_FAILURE,
        )
        self.assertEqual(
            change_log.before_snapshot["codename"],
            self.callcenter.codename,
        )
        self.assertEqual(
            change_log.before_snapshot["days"][Weekday.THURSDAY],
            [],
        )
        self.assertEqual(
            change_log.after_snapshot["days"][Weekday.THURSDAY],
            [
                {
                    "start": "08:00",
                    "end": "12:00",
                },
                {
                    "start": "14:00",
                    "end": "18:00",
                },
            ],
        )
        self.assertEqual(
            change_log.ip_address,
            "127.0.0.10",
        )
        self.assertEqual(
            change_log.user_agent,
            "Schedule test browser",
        )

    def test_same_schedule_does_not_create_duplicate_audit_log(self):
        self.post_schedule(
            [Weekday.FRIDAY],
            ["08:00"],
            ["12:00"],
            "Ajuste operativo",
        )

        response = self.post_schedule(
            [Weekday.FRIDAY],
            ["08:00"],
            ["12:00"],
            "Ajuste repetido",
        )

        self.assertRedirects(
            response,
            f"{self.url}?day={Weekday.MONDAY}&saved=unchanged",
        )
        self.assertEqual(
            ScheduleInterval.objects.count(),
            1,
        )
        self.assertEqual(
            ScheduleChangeLog.objects.count(),
            1,
        )

    def test_closing_day_updates_current_audio_configuration(self):
        ScheduleInterval.objects.create(
            callcenter=self.callcenter,
            weekday=Weekday.FRIDAY,
            start_time="08:00",
            end_time="12:00",
        )

        response = self.post_schedule(
            [],
            [],
            [],
            "Cierre por reentrenamiento",
            audio_file=ScheduleAudio.STAFF_RETRAINING,
            change_type="cierre",
        )

        self.assertEqual(response.status_code, 302)
        self.callcenter.refresh_from_db()
        self.assertEqual(
            self.callcenter.closed_audio_file,
            ScheduleAudio.STAFF_RETRAINING,
        )
        self.assertEqual(
            ScheduleChangeLog.objects.count(),
            1,
        )

    def test_opening_day_ignores_submitted_audio_change(self):
        response = self.post_schedule(
            [Weekday.TUESDAY],
            ["08:00"],
            ["12:00"],
            "Apertura por operación normal",
            audio_file=ScheduleAudio.STAFF_RETRAINING,
            change_type="apertura",
        )

        self.assertEqual(response.status_code, 302)
        self.callcenter.refresh_from_db()
        self.assertEqual(
            self.callcenter.closed_audio_file,
            ScheduleAudio.TECHNICAL_FAILURE,
        )


class AsteriskStatusViewTests(TestCase):
    def setUp(self):
        self.client_account = Client.objects.create(
            name="Cliente estado Asterisk",
        )
        self.callcenter = CallCenter.objects.create(
            client=self.client_account,
            name="Centro estado Asterisk",
            codename="estado_asterisk",
            timezone="America/Bogota",
            closed_audio_file=ScheduleAudio.STAFF_RETRAINING,
        )
        weekday = list(Weekday.values)[
            datetime.now(ZoneInfo("America/Bogota")).weekday()
        ]
        ScheduleInterval.objects.create(
            callcenter=self.callcenter,
            weekday=weekday,
            start_time="00:00",
            end_time="23:59",
        )

    def get_status(self):
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT is_enabled, is_open, playback_file, timezone
                FROM schedules_asterisk_callcenter_status
                WHERE codename = %s
                """,
                [self.callcenter.codename],
            )
            return cursor.fetchone()

    def test_view_calculates_complete_asterisk_status(self):
        enabled, is_open, audio, timezone_name = self.get_status()

        self.assertTrue(enabled)
        self.assertTrue(is_open)
        self.assertEqual(
            audio,
            "custom/callcenter_manager/reentrenamiento_personal",
        )
        self.assertEqual(timezone_name, "America/Bogota")

    def test_inactive_client_disables_callcenter_for_asterisk(self):
        self.client_account.is_active = False
        self.client_account.save(update_fields=["is_active"])

        enabled, is_open, _audio, _timezone = self.get_status()

        self.assertFalse(enabled)
        self.assertFalse(is_open)
