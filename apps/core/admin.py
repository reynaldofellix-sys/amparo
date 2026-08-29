from django.contrib import admin
from django.utils.text import Truncator

from amparo.admin import json_preview

from .models import AssistantMessage, AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "actor", "object_type", "object_id", "ip_address", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("event_type", "actor__email", "actor__full_name", "object_id", "ip_address")
    readonly_fields = [field.name for field in AuditEvent._meta.fields] + ["metadata_formatted"]
    exclude = ("metadata",)
    list_select_related = ("actor",)
    date_hierarchy = "created_at"
    list_per_page = 100

    @admin.display(description="Metadados")
    def metadata_formatted(self, obj):
        return json_preview(obj.metadata)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AssistantMessage)
class AssistantMessageAdmin(admin.ModelAdmin):
    list_display = ("user", "question_summary", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__email", "question", "answer")
    readonly_fields = ("user", "question", "answer", "created_at", "updated_at")
    list_select_related = ("user",)
    date_hierarchy = "created_at"
    list_per_page = 50

    @admin.display(description="Pergunta", ordering="question")
    def question_summary(self, obj):
        return Truncator(obj.question).chars(90)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
