import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Plan(TimeStampedModel):
    class BillingPeriod(models.TextChoices):
        MONTHLY = "monthly", "Mensal"
        YEARLY = "yearly", "Anual"

    name = models.CharField("nome", max_length=80)
    slug = models.SlugField(unique=True)
    description = models.CharField("descrição", max_length=220)
    price = models.DecimalField("preço", max_digits=10, decimal_places=2)
    billing_period = models.CharField(
        "periodicidade",
        max_length=12,
        choices=BillingPeriod.choices,
        default=BillingPeriod.MONTHLY,
    )
    features = models.JSONField("recursos", default=list)
    is_active = models.BooleanField("ativo", default=True)
    is_recommended = models.BooleanField("recomendado", default=False)
    sort_order = models.PositiveSmallIntegerField("ordem", default=0)
    mercado_pago_plan_id = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["sort_order", "price", "name"]
        constraints = [
            models.CheckConstraint(condition=models.Q(price__gte=0), name="plan_price_nonnegative")
        ]

    def __str__(self):
        return self.name

    @property
    def is_free(self):
        return self.price == Decimal("0.00")

    @property
    def billing_label(self):
        return "ano" if self.billing_period == self.BillingPeriod.YEARLY else "mês"


class Subscription(TimeStampedModel):
    class Provider(models.TextChoices):
        INTERNAL = "internal", "Interno"
        MERCADO_PAGO = "mercado_pago", "Mercado Pago"

    class Status(models.TextChoices):
        PENDING = "pending", "Aguardando pagamento"
        ACTIVE = "active", "Ativa"
        PAUSED = "paused", "Pausada"
        PAST_DUE = "past_due", "Pagamento pendente"
        CANCELLED = "cancelled", "Cancelada"
        EXPIRED = "expired", "Expirada"
        FAILED = "failed", "Falhou"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="subscriptions"
    )
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    provider = models.CharField(max_length=24, choices=Provider.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    provider_subscription_id = models.CharField(max_length=120, null=True, blank=True)
    checkout_url = models.URLField(max_length=500, blank=True)
    idempotency_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["provider", "provider_subscription_id"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_subscription_id"],
                condition=models.Q(provider_subscription_id__isnull=False),
                name="unique_provider_subscription",
            ),
            models.UniqueConstraint(
                fields=["user"],
                condition=models.Q(status__in=["pending", "active", "paused", "past_due"]),
                name="one_open_subscription_per_user",
            ),
        ]

    def __str__(self):
        return f"{self.user} — {self.plan} ({self.status})"

    @property
    def provider_label(self):
        if self.provider == self.Provider.INTERNAL:
            return "AMPARO — sem cobrança"
        return self.get_provider_display()


class PaymentWebhookEvent(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "received", "Recebido"
        PROCESSED = "processed", "Processado"
        IGNORED = "ignored", "Ignorado"
        FAILED = "failed", "Falhou"

    id = models.BigAutoField(primary_key=True)
    provider = models.CharField(max_length=24, choices=Subscription.Provider.choices)
    event_id = models.CharField(max_length=180)
    event_type = models.CharField(max_length=100, blank=True)
    payload = models.JSONField(default=dict)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.RECEIVED)
    error_message = models.CharField(max_length=220, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-received_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "event_id"], name="unique_payment_webhook_event"
            )
        ]

    def __str__(self):
        return f"{self.provider}:{self.event_id}"
