from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from callcenters.models import CallCenter
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


class UserManagementTests(TestCase):
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
        self.superuser = get_user_model().objects.create_superuser(
            username="admin",
            password="Strong-pass-12345",
            email="admin@example.com",
        )
        self.normal_user = get_user_model().objects.create_user(
            username="agent",
            password="Strong-pass-12345",
            client=self.client_a,
        )

    def test_superuser_can_view_user_list(self):
        self.client.force_login(self.superuser)

        response = self.client.get(
            reverse("user_list"),
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertContains(
            response,
            self.normal_user.username,
        )
        self.assertNotContains(
            response,
            self.superuser.username,
        )

    def test_superuser_can_view_create_user_page(self):
        self.client.force_login(self.superuser)

        response = self.client.get("/usuarios/crear/")

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertContains(
            response,
            "Crear usuario",
        )
        self.assertContains(
            response,
            "Call centers disponibles",
        )

    def test_normal_user_cannot_view_user_list(self):
        self.client.force_login(self.normal_user)

        response = self.client.get(
            reverse("user_list"),
        )

        self.assertEqual(
            response.status_code,
            403,
        )

    def test_create_user_assigns_client(self):
        self.client.force_login(self.superuser)

        response = self.client.post(
            reverse("user_create"),
            {
                "username": "new-agent",
                "first_name": "Nuevo",
                "last_name": "Agente",
                "email": "new-agent@example.com",
                "client": self.client_b.pk,
                "is_active": "on",
                "password1": "Strong-pass-12345",
                "password2": "Strong-pass-12345",
            },
        )

        self.assertRedirects(
            response,
            reverse("user_list"),
        )

        created_user = get_user_model().objects.get(
            username="new-agent",
        )

        self.assertEqual(
            created_user.client,
            self.client_b,
        )
        self.assertFalse(created_user.is_staff)
        self.assertFalse(created_user.is_superuser)
        self.assertTrue(created_user.check_password("Strong-pass-12345"))

    def test_create_user_requires_client(self):
        self.client.force_login(self.superuser)

        response = self.client.post(
            reverse("user_create"),
            {
                "username": "missing-client",
                "password1": "Strong-pass-12345",
                "password2": "Strong-pass-12345",
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )
        self.assertContains(
            response,
            "Selecciona un cliente para este usuario.",
        )
        self.assertFalse(
            get_user_model().objects.filter(
                username="missing-client",
            ).exists()
        )

    def test_create_user_ignores_staff_and_superuser_post_data(self):
        self.client.force_login(self.superuser)

        response = self.client.post(
            reverse("user_create"),
            {
                "username": "malicious-agent",
                "client": self.client_a.pk,
                "is_active": "on",
                "is_staff": "on",
                "is_superuser": "on",
                "password1": "Strong-pass-12345",
                "password2": "Strong-pass-12345",
            },
        )

        self.assertRedirects(
            response,
            reverse("user_list"),
        )

        created_user = get_user_model().objects.get(
            username="malicious-agent",
        )

        self.assertFalse(created_user.is_staff)
        self.assertFalse(created_user.is_superuser)

    def test_created_user_sees_client_callcenters(self):
        user = get_user_model().objects.create_user(
            username="client-b-agent",
            password="Strong-pass-12345",
            client=self.client_b,
        )
        self.client.force_login(user)

        response = self.client.get(
            reverse("callcenters:list"),
        )

        self.assertContains(
            response,
            self.callcenter_b.name,
        )
        self.assertNotContains(
            response,
            self.callcenter_a.name,
        )

    def test_edit_user_changes_client(self):
        self.client.force_login(self.superuser)

        response = self.client.post(
            reverse(
                "user_update",
                kwargs={
                    "pk": self.normal_user.pk,
                },
            ),
            {
                "username": self.normal_user.username,
                "first_name": "Agente",
                "last_name": "Actualizado",
                "email": "agent@example.com",
                "client": self.client_b.pk,
                "is_active": "on",
            },
        )

        self.assertRedirects(
            response,
            reverse("user_list"),
        )
        self.normal_user.refresh_from_db()
        self.assertEqual(
            self.normal_user.client,
            self.client_b,
        )

    def test_cannot_edit_superuser(self):
        self.client.force_login(self.superuser)

        response = self.client.get(
            reverse(
                "user_update",
                kwargs={
                    "pk": self.superuser.pk,
                },
            ),
        )

        self.assertEqual(
            response.status_code,
            404,
        )

    def test_password_change_updates_password(self):
        self.client.force_login(self.superuser)

        response = self.client.post(
            reverse(
                "user_password_update",
                kwargs={
                    "pk": self.normal_user.pk,
                },
            ),
            {
                "new_password1": "New-strong-pass-12345",
                "new_password2": "New-strong-pass-12345",
            },
        )

        self.assertRedirects(
            response,
            reverse(
                "user_update",
                kwargs={
                    "pk": self.normal_user.pk,
                },
            ),
        )
        self.normal_user.refresh_from_db()
        self.assertTrue(
            self.normal_user.check_password(
                "New-strong-pass-12345",
            )
        )
