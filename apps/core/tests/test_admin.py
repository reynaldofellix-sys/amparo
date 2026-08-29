from decimal import Decimal

from django.contrib import admin
from django.test import RequestFactory, TestCase
from django.urls import reverse

from amparo.admin import AmparoAdminSite
from apps.accounts.models import User
from apps.banking.models import FinancialAccount, LedgerEntry, PaymentCard, Transfer
from apps.banking.services import credit_account
from apps.core.models import AssistantMessage, AuditEvent
from apps.subscriptions.models import PaymentWebhookEvent, Plan, Subscription


class AdminBackofficeTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            email="admin@example.com",
            password="SenhaAdministrativa2026!",
            full_name="Administração AMPARO",
        )
        self.person = User.objects.create_user(
            email="pessoa@example.com",
            password="SenhaSegura2026!",
            full_name="Pessoa de Teste",
            age_group=User.AgeGroup.SENIOR,
        )
        plan = Plan.objects.get(slug="gratuito")
        self.subscription = Subscription.objects.create(
            user=self.person,
            plan=plan,
            provider=Subscription.Provider.INTERNAL,
            status=Subscription.Status.ACTIVE,
        )
        self.transfer = Transfer.objects.create(
            account=self.person.financial_account,
            recipient_name="Contato Seguro",
            pix_key="contato@example.com",
            amount=Decimal("25.00"),
        )
        self.ledger_entry = credit_account(
            account=self.person.financial_account,
            amount=Decimal("100.00"),
            description="Crédito administrativo de teste",
            reference="admin:test:credit",
        )
        self.card = PaymentCard.objects.create(account=self.person.financial_account)
        self.audit_event = AuditEvent.objects.create(
            event_type="admin.test", actor=self.superuser
        )
        self.assistant_message = AssistantMessage.objects.create(
            user=self.person,
            question="Como posso me proteger?",
            answer="Confira os dados antes de continuar.",
        )
        self.webhook_event = PaymentWebhookEvent.objects.create(
            provider=Subscription.Provider.MERCADO_PAGO,
            event_id="event-admin-test",
            status=PaymentWebhookEvent.Status.FAILED,
        )

    def test_custom_admin_dashboard_has_brand_and_operational_metrics(self):
        self.client.force_login(self.superuser)

        response = self.client.get(reverse("admin:index"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/amparo_index.html")
        self.assertContains(response, "Central de administração")
        self.assertContains(response, "Visão geral do AMPARO")
        self.assertContains(response, "Falhas de pagamento")
        self.assertEqual(response.context["amparo_metrics"]["users"], 2)
        self.assertEqual(response.context["amparo_metrics"]["pending_transfers"], 1)
        self.assertEqual(response.context["amparo_metrics"]["active_subscriptions"], 1)
        self.assertEqual(response.context["amparo_metrics"]["failed_webhooks"], 1)

    def test_admin_requires_staff_permission(self):
        self.client.force_login(self.person)

        response = self.client.get(reverse("admin:index"))

        self.assertRedirects(response, f"{reverse('admin:login')}?next={reverse('admin:index')}")

    def test_admin_login_has_accessible_heading_and_brand(self):
        response = self.client.get(reverse("admin:login"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "admin/amparo_login.html")
        self.assertContains(response, "Entrar na administração")
        self.assertContains(response, "ACESSO RESTRITO")

    def test_custom_site_registers_every_operational_model(self):
        self.assertIsInstance(admin.site, AmparoAdminSite)
        expected_models = {
            User,
            FinancialAccount,
            LedgerEntry,
            Transfer,
            PaymentCard,
            AssistantMessage,
            AuditEvent,
            Plan,
            Subscription,
            PaymentWebhookEvent,
        }
        self.assertTrue(expected_models.issubset(admin.site._registry))

    def test_financial_history_and_audit_records_cannot_be_added_or_deleted(self):
        request = RequestFactory().get(reverse("admin:index"))
        request.user = self.superuser

        for model in (LedgerEntry, Transfer, AuditEvent, PaymentWebhookEvent):
            with self.subTest(model=model.__name__):
                model_admin = admin.site._registry[model]
                self.assertFalse(model_admin.has_add_permission(request))
                self.assertFalse(model_admin.has_delete_permission(request))

    def test_person_admin_supports_search_and_related_operational_data(self):
        self.client.force_login(self.superuser)

        changelist = self.client.get(reverse("admin:accounts_user_changelist"), {"q": "Pessoa"})
        detail = self.client.get(reverse("admin:accounts_user_change", args=[self.person.pk]))

        self.assertContains(changelist, "pessoa@example.com")
        self.assertContains(detail, "Conta demonstrativa")
        self.assertContains(detail, "Histórico de assinaturas")

    def test_operational_record_pages_render_with_protected_history(self):
        self.client.force_login(self.superuser)
        records = (
            self.person.financial_account,
            self.ledger_entry,
            self.transfer,
            self.card,
            self.audit_event,
            self.assistant_message,
            self.subscription,
            self.webhook_event,
        )

        for record in records:
            with self.subTest(model=record._meta.model_name):
                url_name = (
                    f"admin:{record._meta.app_label}_{record._meta.model_name}_change"
                )
                response = self.client.get(reverse(url_name, args=[record.pk]))
                self.assertEqual(response.status_code, 200)
