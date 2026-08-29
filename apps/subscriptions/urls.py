from django.urls import path

from . import views

app_name = "subscriptions"

urlpatterns = [
    path("planos/", views.plans, name="plans"),
    path("planos/<slug:slug>/assinar/", views.subscribe, name="subscribe"),
    path("minha-assinatura/", views.subscription_status, name="status"),
    path("webhooks/mercado-pago/", views.mercado_pago_webhook, name="mercado-pago-webhook"),
]
