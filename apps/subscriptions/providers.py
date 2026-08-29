import hashlib
import hmac
from dataclasses import dataclass

import requests
from django.conf import settings


class PaymentProviderError(Exception):
    pass


class PaymentProviderConfigurationError(PaymentProviderError):
    pass


@dataclass(frozen=True)
class CheckoutSession:
    external_id: str
    checkout_url: str
    status: str


class MercadoPagoProvider:
    api_url = "https://api.mercadopago.com"

    def __init__(self, access_token=None, webhook_secret=None, session=None):
        self.access_token = access_token or settings.MERCADO_PAGO_ACCESS_TOKEN
        self.webhook_secret = webhook_secret or settings.MERCADO_PAGO_WEBHOOK_SECRET
        self.session = session or requests.Session()

    @property
    def configured(self):
        return bool(self.access_token)

    def _headers(self, idempotency_key=None):
        if not self.access_token:
            raise PaymentProviderConfigurationError(
                "As credenciais do Mercado Pago ainda não foram configuradas."
            )
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        if idempotency_key:
            headers["X-Idempotency-Key"] = str(idempotency_key)
        return headers

    def create_subscription(self, subscription, return_url):
        plan = subscription.plan
        payload = {
            "reason": f"Plano {plan.name} — AMPARO",
            "external_reference": str(subscription.pk),
            "payer_email": subscription.user.email,
            "back_url": return_url,
            "status": "pending",
        }
        if plan.mercado_pago_plan_id:
            payload["preapproval_plan_id"] = plan.mercado_pago_plan_id
        else:
            payload["auto_recurring"] = {
                "frequency": 1,
                "frequency_type": (
                    "years" if plan.billing_period == plan.BillingPeriod.YEARLY else "months"
                ),
                "transaction_amount": float(plan.price),
                "currency_id": "BRL",
            }
        try:
            response = self.session.post(
                f"{self.api_url}/preapproval",
                headers=self._headers(subscription.idempotency_key),
                json=payload,
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise PaymentProviderError(
                "Não foi possível iniciar o pagamento agora. Tente novamente em instantes."
            ) from exc
        checkout_url = data.get("init_point") or ""
        external_id = data.get("id") or ""
        if not checkout_url or not external_id:
            raise PaymentProviderError("O Mercado Pago retornou uma resposta incompleta.")
        return CheckoutSession(
            external_id=external_id,
            checkout_url=checkout_url,
            status=data.get("status", "pending"),
        )

    def fetch_subscription(self, external_id):
        try:
            response = self.session.get(
                f"{self.api_url}/preapproval/{external_id}",
                headers=self._headers(),
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            raise PaymentProviderError("Não foi possível consultar a assinatura.") from exc

    def validate_webhook(self, x_signature, x_request_id, data_id):
        if not self.webhook_secret:
            raise PaymentProviderConfigurationError(
                "A chave de assinatura dos webhooks não foi configurada."
            )
        parts = {}
        for item in (x_signature or "").split(","):
            key, separator, value = item.strip().partition("=")
            if separator:
                parts[key] = value
        timestamp = parts.get("ts")
        signature = parts.get("v1")
        if not timestamp or not signature or not x_request_id or not data_id:
            return False
        manifest = f"id:{str(data_id).lower()};request-id:{x_request_id};ts:{timestamp};"
        expected = hmac.new(
            self.webhook_secret.encode(), manifest.encode(), hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected, signature)


def get_payment_provider():
    if settings.PAYMENT_PROVIDER == "mercado_pago":
        return MercadoPagoProvider()
    raise PaymentProviderConfigurationError("Gateway de pagamento não suportada.")
