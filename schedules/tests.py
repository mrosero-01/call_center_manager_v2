from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from callcenters.models import CallCenter
from clients.models import Client

from .models import ScheduleChangeLog, ScheduleInterval, Weekday


class ScheduleEditorTests(TestCase):
    def setUp(self):
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

    def post_schedule(self, weekdays, starts, ends, reason):
        return self.client.post(
            self.url,
            {
                "weekday": weekdays,
                "start_time": starts,
                "end_time": ends,
                "change_reason": reason,
            },
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
        self.assertEqual(
            ScheduleChangeLog.objects.count(),
            0,
        )

    def test_allows_more_than_two_intervals_per_day(self):
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
            302,
        )
        self.assertEqual(
            ScheduleInterval.objects.filter(
                callcenter=self.callcenter,
                weekday=Weekday.MONDAY,
            ).count(),
            3,
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
            "debe ser anterior a la hora final",
        )
        self.assertEqual(
            ScheduleInterval.objects.count(),
            0,
        )

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
