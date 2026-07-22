from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from clients.models import Client
from schedules.models import (
    ScheduleChangeLog,
    ScheduleInterval,
    Weekday,
)

from .models import CallCenter


class CallCenterListTests(TestCase):
    def setUp(self):
        self.client_a = Client.objects.create(
            name="Cliente A",
        )
        self.client_b = Client.objects.create(
            name="Cliente B",
        )
        self.callcenter_a = CallCenter.objects.create(
            client=self.client_a,
            name="Campaña A",
            codename="campana_a",
        )
        self.callcenter_b = CallCenter.objects.create(
            client=self.client_b,
            name="Campaña B",
            codename="campana_b",
        )
        ScheduleInterval.objects.create(
            callcenter=self.callcenter_a,
            weekday=Weekday.MONDAY,
            start_time="08:00",
            end_time="12:00",
        )
        ScheduleChangeLog.objects.create(
            callcenter=self.callcenter_a,
            reason="Ajuste operativo",
            before_snapshot={},
            after_snapshot={},
        )
        self.url = reverse("callcenters:list")

    def test_normal_user_only_sees_own_client_callcenters(self):
        user = get_user_model().objects.create_user(
            username="agent-a",
            password="password",
            client=self.client_a,
        )
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertContains(
            response,
            self.callcenter_a.name,
        )
        self.assertNotContains(
            response,
            self.callcenter_b.name,
        )
        self.assertContains(
            response,
            "Con horario",
        )
        self.assertContains(
            response,
            "Último cambio",
        )

    def test_superuser_sees_all_callcenters(self):
        user = get_user_model().objects.create_superuser(
            username="admin",
            password="password",
        )
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertContains(
            response,
            self.callcenter_a.name,
        )
        self.assertContains(
            response,
            self.callcenter_b.name,
        )

    def test_normal_user_cannot_see_inactive_callcenter(self):
        self.callcenter_a.is_active = False
        self.callcenter_a.save(update_fields=["is_active"])
        user = get_user_model().objects.create_user(
            username="agent-inactive-callcenter",
            password="password",
            client=self.client_a,
        )
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertNotContains(response, self.callcenter_a.name)

    def test_normal_user_cannot_see_callcenters_of_inactive_client(self):
        self.client_a.is_active = False
        self.client_a.save(update_fields=["is_active"])
        user = get_user_model().objects.create_user(
            username="agent-inactive-client",
            password="password",
            client=self.client_a,
        )
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertNotContains(response, self.callcenter_a.name)


class ConfigurationManagementTests(TestCase):
    def setUp(self):
        self.admin = get_user_model().objects.create_superuser(
            username="configuration-admin",
            password="password",
        )
        self.client_record = Client.objects.create(name="Cliente existente")
        self.normal_user = get_user_model().objects.create_user(
            username="configuration-user",
            password="password",
            client=self.client_record,
        )
        self.callcenter = CallCenter.objects.create(
            client=self.client_record,
            name="Centro existente",
            codename="centro_existente",
        )
        self.dashboard_url = reverse("management:dashboard")

    def test_dashboard_requires_login(self):
        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_dashboard_rejects_non_superuser(self):
        self.client.force_login(self.normal_user)

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 403)

    def test_superuser_can_open_dashboard(self):
        self.client.force_login(self.admin)

        response = self.client.get(self.dashboard_url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cliente existente")
        self.assertContains(response, "Centro existente")

    def test_superuser_can_create_client(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("management:client_create"),
            {
                "name": "Nuevo cliente",
                "description": "Operación nacional",
                "is_active": "on",
            },
        )

        self.assertRedirects(response, self.dashboard_url)
        self.assertTrue(Client.objects.filter(name="Nuevo cliente").exists())

    def test_client_name_is_unique_ignoring_case(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("management:client_create"),
            {"name": "cliente EXISTENTE", "is_active": "on"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ya existe un cliente")

    def test_superuser_can_create_callcenter(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("management:callcenter_create"),
            {
                "client": self.client_record.pk,
                "name": "Pasto soporte",
                "codename": "PASTO_SOPORTE",
                "timezone": "America/Bogota",
                "closed_audio_file": "reentrenamiento_personal",
                "is_active": "on",
            },
        )

        self.assertRedirects(response, self.dashboard_url)
        created = CallCenter.objects.get(codename="pasto_soporte")
        self.assertEqual(created.client, self.client_record)
        self.assertEqual(created.closed_audio_file, "reentrenamiento_personal")

    def test_invalid_timezone_is_rejected(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("management:callcenter_create"),
            {
                "client": self.client_record.pk,
                "name": "Centro inválido",
                "codename": "centro_invalido",
                "timezone": "Zona/Inventada",
                "closed_audio_file": "falla_tecnica",
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "zona horaria válida")
        self.assertFalse(CallCenter.objects.filter(codename="centro_invalido").exists())

    def test_codename_cannot_be_changed_from_update(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("management:callcenter_update", args=[self.callcenter.pk]),
            {
                "client": self.client_record.pk,
                "name": "Centro actualizado",
                "codename": "codigo_manipulado",
                "timezone": "America/Bogota",
                "closed_audio_file": "falla_tecnica",
                "is_active": "on",
            },
        )

        self.assertRedirects(response, self.dashboard_url)
        self.callcenter.refresh_from_db()
        self.assertEqual(self.callcenter.codename, "centro_existente")
        self.assertEqual(self.callcenter.name, "Centro actualizado")
