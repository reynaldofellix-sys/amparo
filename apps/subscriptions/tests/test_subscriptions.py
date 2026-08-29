import hashlib
import hmac
import json
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import User
from apps.subscriptions.models import PaymentWebhookEvent, Plan, Subscription
from apps.subscriptions.providers import (
    CheckoutSession,
    MercadoPagoProvider,
    PaymentProviderError,
)
from apps.subscriptions.services import SubscriptionConflictError, start_subscription


class SubscriptionServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="planos@example.com", password="UmaSenhaForte2026!", full_name="Pessoa Planos"
        )
        self.free_plan = Plan.objects.get(slug="gratuito")
        self.paid_plan = Plan.objects.get(slug="cuidado")

    def test_free_plan_is_activated_without_gateway(self):
        subscription = start_subscription(
            user=self.user,
            plan=self.free_plan,
            return_url="https://amparo.example/minha-assinatura/",
        )

        self.assertEqual(subscription.status, Subscription.Status.ACTIVE)
        self.assertEqual(subscription.provider, Subscription.Provider.INTERNAL)
        self.assertEqual(subscription.checkout_url, "")

    def test_paid_plan_uses_provider_without_exposing_payment_data(self):
        provider = Mock()
        provider.create_subscription.return_value = CheckoutSession(
            external_id="mp-sub-123",
            checkout_url="https://www.mercadopago.com.br/subscriptions/checkout/test",
            status="pending",
        )

        subscription = start_subscription(
            user=self.user,
            plan=self.paid_plan,
            return_url="https://amparo.example/minha-assinatura/",
            provider=provider,
        )

        self.assertEqual(subscription.provider_subscription_id, "mp-sub-123")
        self.assertNotIn("card", subscription.metadata)
        provider.create_subscription.assert_called_once()

    def test_switching_plan_closes_previous_open_subscription(self):
        old = start_subscription(
            user=self.user,
            plan=self.free_plan,
            return_url="https://amparo.example/minha-assinatura/",
        )
        provider = Mock()
        provider.create_subscription.return_value = CheckoutSession(
            external_id="mp-sub-456", checkout_url="https://example.com/pay", status="pending"
        )

        new = start_subscription(
            user=self.user,
            plan=self.paid_plan,
            return_url="https://amparo.example/minha-assinatura/",
            provider=provider,
        )

        old.refresh_from_db()
        self.assertEqual(old.status, Subscription.Status.CANCELLED)
        self.assertEqual(new.status, Subscription.Status.PENDING)

    def test_paid_subscription_is_reused_instead_of_double_charged(self):
        provider = Mock()
        provider.create_subscription.return_value = CheckoutSession(
            external_id="mp-sub-reused",
            checkout_url="https://example.com/pay",
            status="pending",
        )
        first = start_subscription(
            user=self.user,
            plan=self.paid_plan,
            return_url="https://amparo.example/minha-assinatura/",
            provider=provider,
        )

        second = start_subscription(
            user=self.user,
            plan=self.paid_plan,
            return_url="https://amparo.example/minha-assinatura/",
            provider=provider,
        )

        self.assertEqual(first.pk, second.pk)
        provider.create_subscription.assert_called_once()

    def test_paid_subscription_cannot_be_replaced_without_cancellation(self):
        Subscription.objects.create(
            user=self.user,
            plan=self.paid_plan,
            provider=Subscription.Provider.MERCADO_PAGO,
            status=Subscription.Status.ACTIVE,
            provider_subscription_id="mp-active",
        )

        with self.assertRaises(SubscriptionConflictError):
            start_subscription(
                user=self.user,
                plan=self.free_plan,
                return_url="https://amparo.example/minha-assinatura/",
            )

    def test_gateway_failure_restores_previous_free_plan(self):
        previous = start_subscription(
            user=self.user,
            plan=self.free_plan,
            return_url="https://amparo.example/minha-assinatura/",
        )
        provider = Mock()
        provider.create_subscription.side_effect = PaymentProviderError("indisponível")

        with self.assertRaises(PaymentProviderError):
            start_subscription(
                user=self.user,
                plan=self.paid_plan,
                return_url="https://amparo.example/minha-assinatura/",
                provider=provider,
            )

        previous.refresh_from_db()
        self.assertEqual(previous.status, Subscription.Status.ACTIVE)
        self.assertEqual(
            self.user.subscriptions.filter(status=Subscription.Status.FAILED).count(), 1
        )


class PlansViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="webplanos@example.com",
            password="UmaSenhaForte2026!",
            full_name="Pessoa Web Planos",
        )

    def test_plans_are_public_and_clear(self):
        response = self.client.get(reverse("subscriptions:plans"))

        self.assertContains(response, "Planos simples e transparentes")
        self.assertContains(response, "Grátis")
        self.assertContains(response, "por mês")
        self.assertContains(response, "Pagamento protegido")

    def test_authenticated_user_can_activate_free_plan(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("subscriptions:subscribe", kwargs={"slug": "gratuito"})
        )

        self.assertRedirects(response, reverse("subscriptions:status"))
        self.assertEqual(self.user.subscriptions.get().status, Subscription.Status.ACTIVE)

    def test_incomplete_user_must_finish_onboarding(self):
        self.user.onboarding_completed = False
        self.user.save(update_fields=["onboarding_completed"])
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard"))

        self.assertRedirects(response, reverse("accounts:onboarding"))


class MercadoPagoSecurityTests(TestCase):
    def test_checkout_request_is_idempotent_and_uses_hosted_url(self):
        user = User.objects.create_user(
            email="checkout@example.com", password="UmaSenhaForte2026!", full_name="Checkout"
        )
        subscription = Subscription.objects.create(
            user=user,
            plan=Plan.objects.get(slug="cuidado"),
            provider=Subscription.Provider.MERCADO_PAGO,
        )
        response = Mock()
        response.json.return_value = {
            "id": "mp-checkout-1",
            "init_point": "https://www.mercadopago.com.br/subscriptions/checkout/secure",
            "status": "pending",
        }
        session = Mock()
        session.post.return_value = response
        provider = MercadoPagoProvider(access_token="token", session=session)

        checkout = provider.create_subscription(
            subscription, "https://amparo.example/minha-assinatura/"
        )

        self.assertEqual(checkout.external_id, "mp-checkout-1")
        request = session.post.call_args
        self.assertEqual(
            request.kwargs["headers"]["X-Idempotency-Key"],
            str(subscription.idempotency_key),
        )
        self.assertEqual(request.kwargs["json"]["payer_email"], user.email)
        self.assertNotIn("card", request.kwargs["json"])

    def test_webhook_signature_uses_official_manifest(self):
        provider = MercadoPagoProvider(access_token="token", webhook_secret="secret")
        timestamp = "1704908010"
        request_id = "request-123"
        data_id = "MP-SUB-1"
        manifest = "id:mp-sub-1;request-id:request-123;ts:1704908010;"
        signature = hmac.new(b"secret", manifest.encode(), hashlib.sha256).hexdigest()

        self.assertTrue(
            provider.validate_webhook(
                f"ts={timestamp},v1={signature}", request_id, data_id
            )
        )
        self.assertFalse(
            provider.validate_webhook(f"ts={timestamp},v1=invalid", request_id, data_id)
        )

    @override_settings(
        MERCADO_PAGO_ACCESS_TOKEN="token", MERCADO_PAGO_WEBHOOK_SECRET="secret"
    )
    @patch("apps.subscriptions.providers.MercadoPagoProvider.fetch_subscription")
    def test_webhook_updates_subscription_once(self, fetch_subscription):
        user = User.objects.create_user(
            email="webhook@example.com", password="UmaSenhaForte2026!", full_name="Webhook"
        )
        subscription = Subscription.objects.create(
            user=user,
            plan=Plan.objects.get(slug="cuidado"),
            provider=Subscription.Provider.MERCADO_PAGO,
            status=Subscription.Status.PENDING,
        )
        fetch_subscription.return_value = {
            "id": "mp-sub-1",
            "external_reference": str(subscription.pk),
            "status": "authorized",
        }
        payload = {"id": 9988, "action": "subscription.updated", "data": {"id": "mp-sub-1"}}
        timestamp = "1704908010"
        request_id = "request-456"
        manifest = f"id:mp-sub-1;request-id:{request_id};ts:{timestamp};"
        signature = hmac.new(b"secret", manifest.encode(), hashlib.sha256).hexdigest()
        url = f"{reverse('subscriptions:mercado-pago-webhook')}?data.id=mp-sub-1"
        headers = {
            "HTTP_X_SIGNATURE": f"ts={timestamp},v1={signature}",
            "HTTP_X_REQUEST_ID": request_id,
        }

        first = self.client.post(
            url, data=json.dumps(payload), content_type="application/json", **headers
        )
        second = self.client.post(
            url, data=json.dumps(payload), content_type="application/json", **headers
        )

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, Subscription.Status.ACTIVE)
        self.assertEqual(PaymentWebhookEvent.objects.count(), 1)
        fetch_subscription.assert_called_once_with("mp-sub-1")
