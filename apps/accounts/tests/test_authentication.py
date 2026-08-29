from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User


class AuthenticationTests(TestCase):
    def test_registration_hashes_password_and_creates_account(self):
        response = self.client.post(
            reverse("accounts:register"),
            {
                "full_name": "Maria da Silva",
                "email": "MARIA@example.com",
                "phone": "(88) 99999-0000",
                "age_group": User.AgeGroup.SENIOR,
                "password1": "UmaSenhaForte2026!",
                "password2": "UmaSenhaForte2026!",
                "consent": "on",
            },
        )
        self.assertRedirects(response, reverse("dashboard"))
        user = User.objects.get(email="maria@example.com")
        self.assertNotEqual(user.password, "UmaSenhaForte2026!")
        self.assertTrue(user.check_password("UmaSenhaForte2026!"))
        self.assertEqual(user.financial_account.balance, 0)

    def test_dashboard_requires_authentication(self):
        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, f"{reverse('accounts:login')}?next={reverse('dashboard')}")

    def test_login_does_not_allow_external_redirect(self):
        User.objects.create_user(
            email="safe@example.com", password="UmaSenhaForte2026!", full_name="Conta Segura"
        )
        response = self.client.post(
            f"{reverse('accounts:login')}?next=https://evil.example/",
            {"email": "safe@example.com", "password": "UmaSenhaForte2026!"},
        )
        self.assertRedirects(response, reverse("dashboard"))

    def test_login_is_blocked_after_repeated_failures(self):
        User.objects.create_user(
            email="limite@example.com", password="UmaSenhaForte2026!", full_name="Conta Limite"
        )
        for _ in range(5):
            self.client.post(
                reverse("accounts:login"),
                {"email": "limite@example.com", "password": "senha-incorreta"},
            )
        response = self.client.post(
            reverse("accounts:login"),
            {"email": "limite@example.com", "password": "UmaSenhaForte2026!"},
        )
        self.assertContains(response, "Muitas tentativas", status_code=200)
