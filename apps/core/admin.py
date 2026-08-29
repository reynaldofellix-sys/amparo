from django.contrib import admin

from .models import AssistantMessage, AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "actor", "object_type", "object_id", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("actor__email", "object_id")
    readonly_fields = [field.name for field in AuditEvent._meta.fields]


@admin.register(AssistantMessage)
class AssistantMessageAdmin(admin.ModelAdmin):
    list_display = ("user", "question", "created_at")
    search_fields = ("user__email", "question", "answer")
    readonly_fields = ("user", "question", "answer", "created_at", "updated_at")
