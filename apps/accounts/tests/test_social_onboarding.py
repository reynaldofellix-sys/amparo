from types import SimpleNamespace

from django.test import TestCase, override_settings
from django.test.client import RequestFactory
from django.urls import reverse

from apps.accounts.adapters import AmparoSocialAccountAdapter
from apps.accounts.models import User


class SocialOnboardingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="google@example.com",
            password=None,
            full_name="Pessoa Google",
            onboarding_completed=False,
        )
        self.client.force_login(self.user)

    def test_onboarding_completes_profile_and_can_create_password(self):
        response = self.client.post(
            reverse("accounts:onboarding"),
            {
                "full_name": "Pessoa Google Completa",
                "phone": "(85) 99999-1111",
                "age_group": User.AgeGroup.SENIOR,
                "large_text": "on",
                "password1": "SenhaGoogleForte2026!",
                "password2": "SenhaGoogleForte2026!",
                "consent": "on",
            },
        )

        self.assertRedirects(response, reverse("subscriptions:plans"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.onboarding_completed)
        self.assertTrue(self.user.check_password("SenhaGoogleForte2026!"))
        self.assertEqual(self.user.phone, "(85) 99999-1111")

    def test_onboarding_allows_google_only_without_local_password(self):
        response = self.client.post(
            reverse("accounts:onboarding"),
            {
                "full_name": "Pessoa Google",
                "phone": "(85) 98888-1111",
                "age_group": User.AgeGroup.ADULT,
                "consent": "on",
            },
        )

        self.assertRedirects(response, reverse("subscriptions:plans"))
        self.user.refresh_from_db()
        self.assertFalse(self.user.has_usable_password())

    def test_incomplete_api_session_receives_actionable_status(self):
        response = self.client.get(reverse("api-v1:me"))

        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["detail"], "onboarding_required")

    @override_settings(
        GOOGLE_OAUTH_CLIENT_ID="client.apps.googleusercontent.com",
        GOOGLE_OAUTH_CLIENT_SECRET="secret",
    )
    def test_google_option_is_rendered_when_credentials_exist(self):
        self.user.onboarding_completed = True
        self.user.save(update_fields=["onboarding_completed"])
        self.client.logout()

        response = self.client.get(reverse("accounts:login"))

        self.assertContains(response, "Continuar com Google")
        self.assertContains(response, reverse("google_login"))

    def test_google_profile_is_normalized_and_requires_onboarding(self):
        adapter = AmparoSocialAccountAdapter()
        sociallogin = SimpleNamespace(user=User())
        request = RequestFactory().get("/")

        user = adapter.populate_user(
            request,
            sociallogin,
            {"email": "PESSOA@EXAMPLE.COM", "name": "Pessoa do Google"},
        )

        self.assertEqual(user.email, "pessoa@example.com")
        self.assertEqual(user.full_name, "Pessoa do Google")
        self.assertFalse(user.onboarding_completed)
