from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from callcenters.models import CallCenter
from clients.models import Client
from schedules.models import ScheduleInterval, Weekday


class HomeDashboardTests(TestCase):
    def setUp(self):
        self.client_a = Client.objects.create(
            name="Cliente A",
        )
        self.client_b = Client.objects.create(
            name="Cliente B",
        )
        self.callcenter_with_schedule = CallCenter.objects.create(
            client=self.client_a,
            name="Campaña con horario",
            codename="campana_con_horario",
        )
        self.callcenter_without_schedule = CallCenter.objects.create(
            client=self.client_a,
            name="Campaña sin horario",
            codename="campana_sin_horario",
        )
        self.other_callcenter = CallCenter.objects.create(
            client=self.client_b,
            name="Campaña externa",
            codename="campana_externa",
        )
        ScheduleInterval.objects.create(
            callcenter=self.callcenter_with_schedule,
            weekday=Weekday.MONDAY,
            start_time="08:00",
            end_time="12:00",
        )
        self.url = reverse("home")

    def test_home_metrics_use_only_visible_callcenters(self):
        user = get_user_model().objects.create_user(
            username="agent",
            password="password",
            client=self.client_a,
        )
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertContains(response, "Call centers")
        self.assertContains(response, "Campaña con horario")
        self.assertContains(response, "Campaña sin horario")
        self.assertNotContains(response, "Campaña externa")
        self.assertEqual(
            response.context["dashboard_summary"],
            {
                "callcenters": 2,
                "active": 2,
                "without_schedule": 1,
            },
        )


class LoginRateLimitTests(TestCase):
    def setUp(self):
        cache.clear()
        self.url = reverse("login")

    def test_login_rate_limit_blocks_repeated_failures(self):
        for _ in range(5):
            response = self.client.post(
                self.url,
                {
                    "username": "missing",
                    "password": "bad-password",
                },
            )

            self.assertEqual(response.status_code, 200)

        response = self.client.post(
            self.url,
            {
                "username": "missing",
                "password": "bad-password",
            },
        )

        self.assertContains(
            response,
            "Demasiados intentos de inicio de sesión",
        )
