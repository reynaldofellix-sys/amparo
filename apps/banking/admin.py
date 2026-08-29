from django.contrib import admin

from .models import FinancialAccount, LedgerEntry, PaymentCard, Transfer


@admin.register(FinancialAccount)
class FinancialAccountAdmin(admin.ModelAdmin):
    list_display = ("owner", "branch", "number", "balance", "status", "created_at")
    list_filter = ("status", "currency")
    search_fields = ("owner__email", "owner__full_name", "number")
    readonly_fields = ("balance", "created_at", "updated_at")


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = ("account", "direction", "amount", "balance_after", "description", "occurred_at")
    list_filter = ("direction", "occurred_at")
    search_fields = ("account__owner__email", "reference", "description")
    readonly_fields = [field.name for field in LedgerEntry._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    list_display = ("recipient_name", "account", "amount", "status", "created_at", "completed_at")
    list_filter = ("status", "created_at")
    search_fields = ("recipient_name", "pix_key", "account__owner__email")
    readonly_fields = ("idempotency_key", "created_at", "updated_at", "completed_at")


@admin.register(PaymentCard)
class PaymentCardAdmin(admin.ModelAdmin):
    list_display = ("account", "status", "last_four", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("account__owner__email", "account__owner__full_name")
    readonly_fields = ("account", "created_at", "updated_at")
