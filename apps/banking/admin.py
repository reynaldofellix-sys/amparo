from django.contrib import admin

from amparo.admin import json_preview, status_badge

from .models import FinancialAccount, LedgerEntry, PaymentCard, Transfer


@admin.register(FinancialAccount)
class FinancialAccountAdmin(admin.ModelAdmin):
    list_display = (
        "owner",
        "account_identifier",
        "formatted_balance",
        "status_label",
        "created_at",
    )
    list_filter = ("status", "currency", "created_at")
    search_fields = ("owner__email", "owner__full_name", "number")
    readonly_fields = (
        "owner",
        "branch",
        "number",
        "balance",
        "currency",
        "created_at",
        "updated_at",
    )
    list_select_related = ("owner",)
    date_hierarchy = "created_at"
    list_per_page = 50

    @admin.display(description="Agência / conta", ordering="number")
    def account_identifier(self, obj):
        return f"{obj.branch} / {obj.number}"

    @admin.display(description="Saldo", ordering="balance")
    def formatted_balance(self, obj):
        return f"R$ {obj.balance:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")

    @admin.display(description="Situação", ordering="status")
    def status_label(self, obj):
        return status_badge(obj.status, obj.get_status_display())

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = (
        "account",
        "direction",
        "amount",
        "balance_after",
        "description",
        "occurred_at",
    )
    list_filter = ("direction", "occurred_at")
    search_fields = ("account__owner__email", "reference", "description")
    readonly_fields = [field.name for field in LedgerEntry._meta.fields] + ["metadata_formatted"]
    exclude = ("metadata",)
    list_select_related = ("account", "account__owner")
    date_hierarchy = "occurred_at"
    list_per_page = 100

    @admin.display(description="Metadados")
    def metadata_formatted(self, obj):
        return json_preview(obj.metadata)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = (
        "recipient_name",
        "account",
        "amount",
        "status_label",
        "created_at",
        "completed_at",
    )
    list_filter = ("status", "created_at")
    search_fields = ("recipient_name", "pix_key", "account__owner__email")
    readonly_fields = [field.name for field in Transfer._meta.fields]
    list_select_related = ("account", "account__owner")
    date_hierarchy = "created_at"
    list_per_page = 50

    @admin.display(description="Situação", ordering="status")
    def status_label(self, obj):
        return status_badge(obj.status, obj.get_status_display())

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PaymentCard)
class PaymentCardAdmin(admin.ModelAdmin):
    list_display = ("account", "status_label", "last_four", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("account__owner__email", "account__owner__full_name")
    readonly_fields = ("account", "created_at", "updated_at")
    list_select_related = ("account", "account__owner")
    date_hierarchy = "created_at"

    @admin.display(description="Situação", ordering="status")
    def status_label(self, obj):
        return status_badge(obj.status, obj.get_status_display())

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
