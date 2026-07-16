from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from clients.models import Client


class RootRedirectTests(TestCase):
    def setUp(self):
        self.client_account = Client.objects.create(
            name="Cliente de prueba",
        )
        self.user = get_user_model().objects.create_user(
            username="agent",
            password="password",
            client=self.client_account,
        )

    def test_root_redirects_to_callcenters(self):
        self.client.force_login(self.user)

        response = self.client.get("/")

        self.assertRedirects(
            response,
            reverse("callcenters:list"),
        )

    def test_successful_login_redirects_to_callcenters(self):
        response = self.client.post(
            reverse("login"),
            {
                "username": "agent",
                "password": "password",
            },
        )

        self.assertRedirects(
            response,
            reverse("callcenters:list"),
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
