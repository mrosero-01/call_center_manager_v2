from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from callcenters.models import CallCenter
from clients.models import Client
from schedules.models import ScheduleChangeLog, Weekday


class AuditViewTests(TestCase):
    def setUp(self):
        self.client_account = Client.objects.create(
            name="Cliente de auditoría",
        )
        self.user = get_user_model().objects.create_user(
            username="agent",
            password="password",
            client=self.client_account,
        )
        self.superuser = get_user_model().objects.create_superuser(
            username="root",
            password="password",
            email="root@example.com",
        )
        self.callcenter = CallCenter.objects.create(
            client=self.client_account,
            name="Campaña auditoría",
            codename="campana_auditoria",
        )
        self.before_snapshot = {
            "version": 1,
            "codename": self.callcenter.codename,
            "timezone": self.callcenter.timezone,
            "days": {
                weekday: []
                for weekday, _label in Weekday.choices
            },
        }
        self.after_snapshot = {
            **self.before_snapshot,
            "days": {
                **self.before_snapshot["days"],
                Weekday.MONDAY: [
                    {
                        "start": "08:00",
                        "end": "12:00",
                    },
                ],
            },
        }
        self.change_log = ScheduleChangeLog.objects.create(
            callcenter=self.callcenter,
            user=self.user,
            reason="Capacitación del personal",
            before_snapshot=self.before_snapshot,
            after_snapshot=self.after_snapshot,
            audio_file="falla_tecnica",
            audio_label="Falla técnica",
            ip_address="127.0.0.20",
            user_agent="Audit test browser",
        )

    def test_normal_user_cannot_access_audit_list(self):
        self.client.force_login(self.user)

        response = self.client.get(
            reverse("audit:list"),
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_superuser_can_access_audit_list(self):
        self.client.force_login(self.superuser)

        response = self.client.get(
            reverse("audit:list"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertContains(
            response,
            "Capacitación del personal",
        )
        self.assertContains(
            response,
            "Campaña auditoría",
        )
        self.assertContains(
            response,
            "Lunes: Cerrado",
        )
        self.assertContains(
            response,
            "08:00 a. m. - 12:00 p. m.",
        )

    def test_superuser_can_see_audit_detail(self):
        self.client.force_login(self.superuser)

        response = self.client.get(
            reverse(
                "audit:detail",
                kwargs={
                    "pk": self.change_log.pk,
                },
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertContains(
            response,
            "Capacitación del personal",
        )
        self.assertContains(
            response,
            "08:00-12:00",
        )
        self.assertContains(
            response,
            "127.0.0.20",
        )
