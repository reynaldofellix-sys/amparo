from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class AmparoUserAdmin(UserAdmin):
    ordering = ("email",)
    list_display = ("email", "full_name", "phone", "age_group", "is_active", "is_staff")
    search_fields = ("email", "full_name", "phone")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Dados pessoais", {"fields": ("full_name", "phone", "age_group")}),
        (
            "Preferências",
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
            "Permissões",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Datas", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "full_name", "password1", "password2", "is_staff"),
            },
        ),
    )
