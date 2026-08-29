from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.banking.models import FinancialAccount
from apps.subscriptions.models import Subscription

from .models import User


class FinancialAccountInline(admin.StackedInline):
    model = FinancialAccount
    can_delete = False
    extra = 0
    max_num = 1
    readonly_fields = (
        "branch",
        "number",
        "balance",
        "currency",
        "status",
        "created_at",
        "updated_at",
    )
    verbose_name = "Conta demonstrativa"
    verbose_name_plural = "Conta demonstrativa"

    def has_add_permission(self, request, obj=None):
        return False


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    can_delete = False
    extra = 0
    show_change_link = True
    fields = ("plan", "provider", "status", "current_period_end", "created_at")
    readonly_fields = fields
    verbose_name_plural = "Histórico de assinaturas"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(User)
class AmparoUserAdmin(UserAdmin):
    ordering = ("-date_joined",)
    list_display = (
        "email",
        "full_name",
        "age_group",
        "account_status",
        "current_plan",
        "onboarding_completed",
        "is_active",
        "is_staff",
        "date_joined",
    )
    list_filter = (
        "is_active",
        "is_staff",
        "is_superuser",
        "onboarding_completed",
        "large_text",
        "age_group",
        "date_joined",
    )
    search_fields = ("email", "full_name", "phone", "financial_account__number")
    readonly_fields = ("last_login", "date_joined")
    date_hierarchy = "date_joined"
    list_per_page = 50
    inlines = (FinancialAccountInline, SubscriptionInline)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Dados pessoais",
            {"fields": ("full_name", "phone", "age_group", "onboarding_completed")},
        ),
        (
            "Acessibilidade e segurança",
            {
                "fields": (
                    "large_text",
                    "transfer_alerts",
                    "login_alerts",
                    "security_alerts",
                    "confirm_transfers",
                )
            },
        ),
        (
            "Permissões administrativas",
            {
                "classes": ("collapse",),
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        ("Datas", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            "Nova pessoa",
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "full_name",
                    "phone",
                    "age_group",
                    "password1",
                    "password2",
                    "is_active",
                    "is_staff",
                ),
            },
        ),
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("financial_account")
            .prefetch_related("subscriptions__plan")
        )

    @admin.display(description="Conta", ordering="financial_account__status")
    def account_status(self, obj):
        try:
            return obj.financial_account.get_status_display()
        except FinancialAccount.DoesNotExist:
            return "Sem conta"

    @admin.display(description="Plano atual")
    def current_plan(self, obj):
        open_statuses = {
            Subscription.Status.PENDING,
            Subscription.Status.ACTIVE,
            Subscription.Status.PAUSED,
            Subscription.Status.PAST_DUE,
        }
        subscription = next(
            (item for item in obj.subscriptions.all() if item.status in open_statuses), None
        )
        return subscription.plan.name if subscription else "Sem plano"
