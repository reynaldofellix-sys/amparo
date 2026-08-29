from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.banking.services import credit_account


class MobileApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="mobile@example.com", password="UmaSenhaForte2026!", full_name="Usuária Mobile"
        )

    def test_private_endpoints_require_authentication(self):
        response = self.client.get(reverse("api-v1:account"))
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["error"]["code"], "authentication_required")

    def test_account_and_movements_are_versioned_json(self):
        credit_account(
            account=self.user.financial_account,
            amount=Decimal("25.00"),
            description="Crédito mobile",
            reference="test:mobile",
        )
        self.client.force_login(self.user)
        account = self.client.get(reverse("api-v1:account")).json()
        movements = self.client.get(reverse("api-v1:movements")).json()
        self.assertEqual(account["balance"], "25.00")
        self.assertTrue(account["demo"])
        self.assertEqual(movements["results"][0]["description"], "Crédito mobile")

    def test_profile_api_does_not_expose_password_or_phone(self):
        self.client.force_login(self.user)
        data = self.client.get(reverse("api-v1:me")).json()
        self.assertNotIn("password", data)
        self.assertNotIn("phone", data)
