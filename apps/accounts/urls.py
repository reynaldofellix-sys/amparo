from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("cadastro/", views.register, name="register"),
    path("entrar/", views.sign_in, name="login"),
    path("sair/", views.sign_out, name="logout"),
    path("perfil/", views.profile, name="profile"),
    path("seguranca/", views.security, name="security"),
    path("completar-cadastro/", views.onboarding, name="onboarding"),
]
