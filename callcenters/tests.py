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

    def test_user_without_client_sees_empty_list(self):
        user = get_user_model().objects.create_user(
            username="agent-empty",
            password="password",
        )
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertContains(
            response,
            "No hay call centers disponibles",
        )
        self.assertNotContains(
            response,
            self.callcenter_a.name,
        )
