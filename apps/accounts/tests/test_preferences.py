from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User


class AccountPreferencesTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="preferencias@example.com",
            password="UmaSenhaForte2026!",
            full_name="Pessoa Preferências",
            phone="(85) 99999-0000",
            age_group=User.AgeGroup.SENIOR,
        )
        self.client.force_login(self.user)

    def test_security_labels_are_clear_and_in_portuguese(self):
        response = self.client.get(reverse("accounts:security"))

        self.assertContains(response, "Alertas de transferência")
        self.assertContains(response, "Alertas de acesso")
        self.assertContains(response, "Alertas de segurança")
        self.assertContains(response, "Confirmar transferências")
        self.assertNotContains(response, "Transfer alerts")
        self.assertNotContains(response, "Login alerts")

    def test_profile_update_preserves_contact_data(self):
        response = self.client.post(
            reverse("accounts:profile"),
            {
                "full_name": "Pessoa Preferências Atualizada",
                "email": self.user.email,
                "phone": self.user.phone,
                "age_group": User.AgeGroup.SENIOR,
                "large_text": "on",
            },
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, "preferencias@example.com")
        self.assertEqual(self.user.phone, "(85) 99999-0000")
        self.assertEqual(self.user.full_name, "Pessoa Preferências Atualizada")
        self.assertTrue(self.user.large_text)

    def test_security_preferences_are_persisted(self):
        response = self.client.post(
            reverse("accounts:security"),
            {
                "transfer_alerts": "on",
                "security_alerts": "on",
                "confirm_transfers": "on",
                "large_text": "on",
            },
        )

        self.assertRedirects(response, reverse("accounts:security"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.transfer_alerts)
        self.assertFalse(self.user.login_alerts)
        self.assertTrue(self.user.security_alerts)
        self.assertTrue(self.user.confirm_transfers)
        self.assertTrue(self.user.large_text)
