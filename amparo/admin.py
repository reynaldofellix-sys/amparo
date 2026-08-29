import json
from datetime import timedelta

from django.contrib.admin import AdminSite
from django.db.models import Sum
from django.utils import timezone
from django.utils.html import format_html


def status_badge(value, label):
    return format_html('<span class="status-pill status-{}">{}</span>', value, label)


def json_preview(value):
    content = json.dumps(value or {}, ensure_ascii=False, indent=2, sort_keys=True)
    return format_html('<pre class="json-preview">{}</pre>', content)


class AmparoAdminSite(AdminSite):
    site_header = "AMPARO — Administração"
    site_title = "AMPARO Admin"
    index_title = "Visão geral da operação"
    index_template = "admin/amparo_index.html"
    login_template = "admin/amparo_login.html"
    site_url = "/"
    enable_nav_sidebar = True
    empty_value_display = "—"

    def index(self, request, extra_context=None):
        from apps.accounts.models import User
        from apps.banking.models import FinancialAccount, Transfer
        from apps.core.models import AuditEvent
        from apps.subscriptions.models import PaymentWebhookEvent, Subscription

        since = timezone.now() - timedelta(hours=24)
        operational_context = {
            "amparo_metrics": {
                "users": User.objects.count(),
                "active_users": User.objects.filter(is_active=True).count(),
                "demo_balance": FinancialAccount.objects.aggregate(total=Sum("balance"))[
                    "total"
                ]
                or 0,
                "pending_transfers": Transfer.objects.filter(
                    status=Transfer.Status.PENDING
                ).count(),
                "active_subscriptions": Subscription.objects.filter(
                    status=Subscription.Status.ACTIVE
                ).count(),
                "failed_webhooks": PaymentWebhookEvent.objects.filter(
                    status=PaymentWebhookEvent.Status.FAILED
                ).count(),
                "audit_events_24h": AuditEvent.objects.filter(created_at__gte=since).count(),
            }
        }
        operational_context.update(extra_context or {})
        return super().index(request, extra_context=operational_context)

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)
        order = {"accounts": 10, "banking": 20, "subscriptions": 30, "core": 40}
        return sorted(app_list, key=lambda app: order.get(app["app_label"], 100))
