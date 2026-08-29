from django.urls import path

from . import views

urlpatterns = [
    path("inicio/", views.dashboard, name="dashboard"),
    path("movimentacoes/", views.transactions, name="transactions"),
    path("minha-conta/", views.account_detail, name="account-detail"),
    path("cartao/", views.card_detail, name="card-detail"),
    path("cartao/solicitar/", views.card_request, name="card-request"),
    path("transferir/", views.transfer_create, name="transfer-create"),
    path("transferir/<uuid:pk>/revisar/", views.transfer_review, name="transfer-review"),
    path("transferir/<uuid:pk>/confirmar/", views.transfer_confirm, name="transfer-confirm"),
    path("transferir/<uuid:pk>/cancelar/", views.transfer_cancel, name="transfer-cancel"),
    path("transferencias/<uuid:pk>/", views.transfer_detail, name="transfer-detail"),
]
