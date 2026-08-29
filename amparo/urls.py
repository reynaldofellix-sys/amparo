from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("autenticacao/", include("allauth.urls")),
    path("api/v1/", include("apps.api.urls")),
    path("conta/", include("apps.accounts.urls")),
    path("", include("apps.subscriptions.urls")),
    path("", include("apps.core.urls")),
    path("", include("apps.banking.urls")),
]
