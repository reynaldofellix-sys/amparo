from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User


class AccessibleInterfaceSmokeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="acessibilidade@example.com",
            password="UmaSenhaForte2026!",
            full_name="Pessoa Acessível",
        )

    def test_public_pages_have_accessibility_controls(self):
        for route in ("landing", "accounts:login", "accounts:register"):
            with self.subTest(route=route):
                response = self.client.get(reverse(route))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Ir para o conteúdo")
                self.assertContains(response, 'lang="pt-BR"')

    def test_authenticated_pages_render_mobile_navigation(self):
        self.client.force_login(self.user)
        routes = (
            "dashboard",
            "transactions",
            "transfer-create",
            "assistant",
            "accounts:profile",
            "accounts:security",
            "account-detail",
            "card-detail",
            "privacy",
        )
        for route in routes:
            with self.subTest(route=route):
                response = self.client.get(reverse(route))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "Navegação principal")
                self.assertContains(response, "data-menu-open")

    def test_current_page_is_exposed_to_assistive_technology(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, 'aria-current="page"')
        self.assertContains(response, "logo-mark.svg")
