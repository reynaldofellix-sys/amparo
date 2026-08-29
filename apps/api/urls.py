from django.urls import path

from . import views

app_name = "api-v1"

urlpatterns = [
    path("health/", views.health, name="health"),
    path("me/", views.me, name="me"),
    path("account/", views.account_summary, name="account"),
    path("movements/", views.movements, name="movements"),
]
