from django.contrib import admin

from .models import PaymentWebhookEvent, Plan, Subscription


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "billing_period", "is_active", "is_recommended")
    list_filter = ("is_active", "billing_period", "is_recommended")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "provider", "status", "created_at")
    list_filter = ("provider", "status", "plan")
    search_fields = ("user__email", "provider_subscription_id")
    readonly_fields = ("idempotency_key", "metadata")


@admin.register(PaymentWebhookEvent)
class PaymentWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("provider", "event_id", "event_type", "status", "received_at")
    list_filter = ("provider", "status", "event_type")
    readonly_fields = ("provider", "event_id", "payload", "received_at", "processed_at")
