from django.db import transaction
from django.utils import timezone

from apps.core.services import audit

from .models import PaymentWebhookEvent, Subscription
from .providers import PaymentProviderError, get_payment_provider

OPEN_STATUSES = (
    Subscription.Status.PENDING,
    Subscription.Status.ACTIVE,
    Subscription.Status.PAUSED,
    Subscription.Status.PAST_DUE,
)

MERCADO_PAGO_STATUS_MAP = {
    "pending": Subscription.Status.PENDING,
    "authorized": Subscription.Status.ACTIVE,
    "paused": Subscription.Status.PAUSED,
    "cancelled": Subscription.Status.CANCELLED,
}


class SubscriptionConflictError(Exception):
    pass


def current_subscription(user):
    return user.subscriptions.filter(status__in=OPEN_STATUSES).select_related("plan").first()


def start_subscription(*, user, plan, return_url, request=None, provider=None):
    previous = None
    with transaction.atomic():
        existing = (
            user.subscriptions.select_for_update().filter(status__in=OPEN_STATUSES).first()
        )
        if existing and existing.plan_id == plan.pk:
            return existing
        if existing:
            if existing.provider == Subscription.Provider.MERCADO_PAGO:
                raise SubscriptionConflictError(
                    "Para trocar este plano, primeiro cancele a assinatura atual."
                )
            previous = existing
            existing.status = Subscription.Status.CANCELLED
            existing.save(update_fields=["status", "updated_at"])
        subscription = Subscription.objects.create(
            user=user,
            plan=plan,
            provider=(
                Subscription.Provider.INTERNAL
                if plan.is_free
                else Subscription.Provider.MERCADO_PAGO
            ),
            status=(Subscription.Status.ACTIVE if plan.is_free else Subscription.Status.PENDING),
        )

    if plan.is_free:
        audit(event_type="subscription.activated", actor=user, request=request, obj=subscription)
        return subscription

    payment_provider = provider or get_payment_provider()
    try:
        checkout = payment_provider.create_subscription(subscription, return_url)
    except PaymentProviderError:
        with transaction.atomic():
            subscription.status = Subscription.Status.FAILED
            subscription.save(update_fields=["status", "updated_at"])
            if previous:
                previous.status = Subscription.Status.ACTIVE
                previous.save(update_fields=["status", "updated_at"])
        raise
    subscription.provider_subscription_id = checkout.external_id
    subscription.checkout_url = checkout.checkout_url
    subscription.metadata = {"provider_status": checkout.status}
    subscription.save(
        update_fields=[
            "provider_subscription_id",
            "checkout_url",
            "metadata",
            "updated_at",
        ]
    )
    audit(event_type="subscription.checkout_started", actor=user, request=request, obj=subscription)
    return subscription


def process_mercado_pago_webhook(*, payload, data_id, event_id, provider):
    event, created = PaymentWebhookEvent.objects.get_or_create(
        provider=Subscription.Provider.MERCADO_PAGO,
        event_id=event_id,
        defaults={"event_type": payload.get("action", ""), "payload": payload},
    )
    if not created:
        return event
    try:
        remote = provider.fetch_subscription(data_id)
        external_reference = remote.get("external_reference")
        subscription = Subscription.objects.filter(pk=external_reference).first()
        if not subscription or subscription.provider != Subscription.Provider.MERCADO_PAGO:
            event.status = PaymentWebhookEvent.Status.IGNORED
        else:
            subscription.provider_subscription_id = remote.get("id") or data_id
            subscription.status = MERCADO_PAGO_STATUS_MAP.get(
                remote.get("status"), Subscription.Status.PAST_DUE
            )
            subscription.metadata = {
                **subscription.metadata,
                "provider_status": remote.get("status", "unknown"),
            }
            subscription.save(
                update_fields=[
                    "provider_subscription_id",
                    "status",
                    "metadata",
                    "updated_at",
                ]
            )
            event.status = PaymentWebhookEvent.Status.PROCESSED
        event.processed_at = timezone.now()
        event.save(update_fields=["status", "processed_at"])
    except Exception as exc:
        event.status = PaymentWebhookEvent.Status.FAILED
        event.error_message = str(exc)[:220]
        event.processed_at = timezone.now()
        event.save(update_fields=["status", "error_message", "processed_at"])
        raise
    return event
