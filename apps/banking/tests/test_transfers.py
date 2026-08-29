import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from apps.accounts.models import User
from apps.banking.models import LedgerEntry, PaymentCard, Transfer
from apps.banking.services import complete_transfer, create_transfer_draft, credit_account


class TransferServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="maria@example.com", password="UmaSenhaForte2026!", full_name="Maria Amparo"
        )
        self.account = self.user.financial_account
        credit_account(
            account=self.account,
            amount=Decimal("1250.00"),
            description="Crédito de teste",
            reference="test:opening",
        )
        self.account.refresh_from_db()

    def draft(self, **overrides):
        data = {
            "account": self.account,
            "recipient_name": "José da Silva",
            "pix_key": "jose@example.com",
            "amount": Decimal("100.00"),
            "idempotency_key": uuid.uuid4(),
        }
        data.update(overrides)
        return create_transfer_draft(**data)

    def test_complete_transfer_debits_once(self):
        transfer = self.draft()
        complete_transfer(transfer_id=transfer.pk, user=self.user)
        complete_transfer(transfer_id=transfer.pk, user=self.user)

        self.account.refresh_from_db()
        transfer.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("1150.00"))
        self.assertEqual(transfer.status, Transfer.Status.COMPLETED)
        self.assertEqual(
            LedgerEntry.objects.filter(reference=f"transfer:{transfer.idempotency_key}").count(), 1
        )

    def test_reusing_key_with_different_payload_is_rejected(self):
        key = uuid.uuid4()
        self.draft(idempotency_key=key)
        with self.assertRaises(ValidationError):
            self.draft(idempotency_key=key, amount=Decimal("200.00"))

    def test_insufficient_funds_does_not_change_ledger(self):
        transfer = self.draft(amount=Decimal("2000.00"))
        before = LedgerEntry.objects.count()
        with self.assertRaises(ValidationError):
            complete_transfer(transfer_id=transfer.pk, user=self.user)
        self.account.refresh_from_db()
        self.assertEqual(self.account.balance, Decimal("1250.00"))
        self.assertEqual(LedgerEntry.objects.count(), before)

    def test_another_user_cannot_complete_transfer(self):
        transfer = self.draft()
        intruder = User.objects.create_user(
            email="intruso@example.com", password="UmaSenhaForte2026!", full_name="Outro Usuário"
        )
        with self.assertRaises(Transfer.DoesNotExist):
            complete_transfer(transfer_id=transfer.pk, user=intruder)


class TransferViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="web@example.com", password="UmaSenhaForte2026!", full_name="Usuário Web"
        )
        self.client.force_login(self.user)

    def test_transfer_review_belongs_to_authenticated_user(self):
        other = User.objects.create_user(
            email="other@example.com", password="UmaSenhaForte2026!", full_name="Outro"
        )
        transfer = Transfer.objects.create(
            account=other.financial_account,
            recipient_name="Destino",
            pix_key="destino@example.com",
            amount=Decimal("10.00"),
        )
        response = self.client.get(reverse("transfer-review", kwargs={"pk": transfer.pk}))
        self.assertEqual(response.status_code, 404)

    def test_card_request_is_idempotent(self):
        url = reverse("card-request")
        self.client.post(url)
        self.client.post(url)
        self.assertEqual(PaymentCard.objects.filter(account=self.user.financial_account).count(), 1)

    def test_complete_transfer_journey(self):
        credit_account(
            account=self.user.financial_account,
            amount=Decimal("50.00"),
            description="Saldo da jornada",
            reference="test:web-opening",
        )
        response = self.client.post(
            reverse("transfer-create"),
            {
                "recipient_name": "Destino Web",
                "pix_key": "destino@web.local",
                "amount": "10.00",
                "request_key": str(uuid.uuid4()),
            },
        )
        transfer = Transfer.objects.get(recipient_name="Destino Web")
        self.assertRedirects(response, reverse("transfer-review", kwargs={"pk": transfer.pk}))

        response = self.client.post(reverse("transfer-confirm", kwargs={"pk": transfer.pk}))
        self.assertRedirects(response, reverse("transfer-detail", kwargs={"pk": transfer.pk}))
        self.user.financial_account.refresh_from_db()
        self.assertEqual(self.user.financial_account.balance, Decimal("40.00"))
