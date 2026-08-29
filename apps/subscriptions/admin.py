from django.contrib import admin

from amparo.admin import json_preview, status_badge

from .models import PaymentWebhookEvent, Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "price",
        "billing_period",
        "is_active",
        "is_recommended",
        "sort_order",
    )
    list_display_links = ("name",)
    list_editable = ("is_active", "is_recommended", "sort_order")
    list_filter = ("is_active", "billing_period", "is_recommended")
    search_fields = ("name", "slug", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Apresentação", {"fields": ("name", "slug", "description", "features")}),
        ("Cobrança", {"fields": ("price", "billing_period", "mercado_pago_plan_id")}),
        ("Publicação", {"fields": ("is_active", "is_recommended", "sort_order")}),
        ("Datas", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "provider", "status_label", "current_period_end", "created_at")
    list_filter = ("provider", "status", "plan")
    search_fields = ("user__email", "user__full_name", "provider_subscription_id")
    readonly_fields = (
        "user",
        "plan",
        "provider",
        "provider_subscription_id",
        "checkout_url",
        "idempotency_key",
        "metadata_formatted",
        "created_at",
        "updated_at",
    )
    exclude = ("metadata",)
    list_select_related = ("user", "plan")
    date_hierarchy = "created_at"
    list_per_page = 50
    fieldsets = (
        ("Pessoa e plano", {"fields": ("user", "plan", "provider", "status")}),
        (
            "Ciclo da assinatura",
            {"fields": ("current_period_end", "cancel_at_period_end")},
        ),
        (
            "Integração",
            {
                "classes": ("collapse",),
                "fields": (
                    "provider_subscription_id",
                    "checkout_url",
                    "idempotency_key",
                    "metadata_formatted",
                ),
            },
        ),
        ("Datas", {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Situação", ordering="status")
    def status_label(self, obj):
        return status_badge(obj.status, obj.get_status_display())

    @admin.display(description="Metadados")
    def metadata_formatted(self, obj):
        return json_preview(obj.metadata)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PaymentWebhookEvent)
class PaymentWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("provider", "event_id", "event_type", "status_label", "received_at")
    list_filter = ("provider", "status", "event_type")
    search_fields = ("event_id", "event_type", "error_message")
    readonly_fields = [field.name for field in PaymentWebhookEvent._meta.fields] + [
        "payload_formatted"
    ]
    exclude = ("payload",)
    date_hierarchy = "received_at"
    list_per_page = 100

    @admin.display(description="Situação", ordering="status")
    def status_label(self, obj):
        return status_badge(obj.status, obj.get_status_display())

    @admin.display(description="Conteúdo recebido")
    def payload_formatted(self, obj):
        return json_preview(obj.payload)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
