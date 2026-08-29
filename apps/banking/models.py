import secrets
import uuid
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from apps.core.models import TimeStampedModel


def generate_account_number():
    return f"{secrets.randbelow(10**8):08d}"


class FinancialAccount(TimeStampedModel):
    class Status(models.TextChoices):
        ACTIVE = "active", "Ativa"
        BLOCKED = "blocked", "Bloqueada"
        CLOSED = "closed", "Encerrada"

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="financial_account"
    )
    branch = models.CharField(max_length=4, default="0001")
    number = models.CharField(max_length=8, unique=True, default=generate_account_number)
    balance = models.DecimalField(max_digits=19, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.ACTIVE)
    currency = models.CharField(max_length=3, default="BRL")

    class Meta:
        verbose_name = "conta demonstrativa"
        verbose_name_plural = "contas demonstrativas"
        indexes = [models.Index(fields=["status", "created_at"])]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(balance__gte=0), name="account_balance_nonnegative"
            )
        ]

    def __str__(self):
        return f"{self.branch}/{self.number} - {self.owner}"


class LedgerEntry(models.Model):
    class Direction(models.TextChoices):
        CREDIT = "credit", "Crédito"
        DEBIT = "debit", "Débito"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account = models.ForeignKey(
        FinancialAccount, on_delete=models.PROTECT, related_name="ledger_entries"
    )
    direction = models.CharField(max_length=8, choices=Direction.choices)
    amount = models.DecimalField(
        max_digits=19, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    balance_after = models.DecimalField(max_digits=19, decimal_places=2)
    description = models.CharField(max_length=180)
    reference = models.CharField(max_length=120)
    metadata = models.JSONField(default=dict, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-occurred_at", "-id"]
        verbose_name = "lançamento financeiro"
        verbose_name_plural = "lançamentos financeiros"
        constraints = [
            models.UniqueConstraint(
                fields=["account", "reference"], name="unique_ledger_reference"
            ),
            models.CheckConstraint(condition=models.Q(amount__gt=0), name="ledger_amount_positive"),
        ]
        indexes = [models.Index(fields=["account", "-occurred_at"])]

    def __str__(self):
        return f"{self.get_direction_display()} {self.amount} - {self.description}"

    def save(self, *args, **kwargs):
        if self.pk and LedgerEntry.objects.filter(pk=self.pk).exists():
            raise ValueError("Lançamentos do ledger são imutáveis.")
        return super().save(*args, **kwargs)


class Transfer(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Aguardando confirmação"
        COMPLETED = "completed", "Concluída"
        CANCELLED = "cancelled", "Cancelada"
        FAILED = "failed", "Falhou"

    account = models.ForeignKey(
        FinancialAccount, on_delete=models.PROTECT, related_name="transfers"
    )
    recipient_name = models.CharField(max_length=180)
    pix_key = models.CharField(max_length=180)
    amount = models.DecimalField(
        max_digits=19, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    idempotency_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    failure_reason = models.CharField(max_length=180, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "transferência Pix"
        verbose_name_plural = "transferências Pix"
        indexes = [
            models.Index(fields=["account", "-created_at"]),
            models.Index(fields=["status", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(amount__gt=0), name="transfer_amount_positive"
            )
        ]

    def __str__(self):
        return f"{self.recipient_name} - {self.amount} ({self.status})"


class PaymentCard(TimeStampedModel):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Solicitado"
        IN_REVIEW = "in_review", "Em análise"
        APPROVED = "approved", "Aprovado"
        ISSUED = "issued", "Emitido"
        BLOCKED = "blocked", "Bloqueado"
        CANCELLED = "cancelled", "Cancelado"

    account = models.OneToOneField(
        FinancialAccount, on_delete=models.PROTECT, related_name="payment_card"
    )
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.REQUESTED)
    last_four = models.CharField(max_length=4, blank=True)

    class Meta:
        verbose_name = "cartão demonstrativo"
        verbose_name_plural = "cartões demonstrativos"

    def __str__(self):
        return f"Cartão de {self.account.owner} — {self.get_status_display()}"
