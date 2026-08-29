from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.core.services import audit

from .forms import (
    EmailAuthenticationForm,
    ProfileForm,
    RegistrationForm,
    SecurityPreferencesForm,
    SocialOnboardingForm,
)
from .services import clear_login_attempts, login_is_blocked, record_failed_login


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            user = form.save()
            user.onboarding_completed = True
            user.save(update_fields=["onboarding_completed"])
            audit(event_type="account.registered", actor=user, request=request, obj=user)
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, "Sua conta demonstrativa foi criada com segurança.")
        return redirect("dashboard")
    return render(request, "accounts/register.html", {"form": form})


def sign_in(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = EmailAuthenticationForm(request, request.POST or None)
    if request.method == "POST":
        email = request.POST.get("email", "")
        if login_is_blocked(request, email):
            form.add_error(None, "Muitas tentativas. Aguarde 15 minutos antes de tentar novamente.")
        elif form.is_valid():
            user = form.get_user()
            clear_login_attempts(request, email)
            login(request, user)
            audit(event_type="account.logged_in", actor=user, request=request, obj=user)
            messages.success(request, "Login realizado com sucesso.")
            next_url = request.GET.get("next")
            if next_url and url_has_allowed_host_and_scheme(
                next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
            ):
                return redirect(next_url)
            return redirect("dashboard")
        else:
            attempts = record_failed_login(request, email)
            audit(
                event_type="account.login_failed",
                request=request,
                metadata={"attempt": attempts},
            )
    return render(request, "accounts/login.html", {"form": form})


@require_POST
def sign_out(request):
    if request.user.is_authenticated:
        audit(
            event_type="account.logged_out", actor=request.user, request=request, obj=request.user
        )
    logout(request)
    messages.info(request, "Você saiu da conta.")
    return redirect("landing")


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        audit(event_type="profile.updated", actor=user, request=request, obj=user)
        messages.success(request, "Perfil atualizado.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"form": form})


@login_required
def security(request):
    form = SecurityPreferencesForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        audit(event_type="security.preferences_updated", actor=user, request=request, obj=user)
        messages.success(request, "Preferências de segurança salvas.")
        return redirect("accounts:security")
    return render(request, "accounts/security.html", {"form": form})


@login_required
def onboarding(request):
    if request.user.onboarding_completed:
        return redirect("dashboard")
    form = SocialOnboardingForm(request.POST or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        had_password = request.user.has_usable_password()
        user = form.save()
        if user.has_usable_password() and not had_password:
            update_session_auth_hash(request, user)
        audit(event_type="account.onboarding_completed", actor=user, request=request, obj=user)
        messages.success(request, "Cadastro concluído. Sua conta está pronta para usar.")
        return redirect("subscriptions:plans")
    return render(request, "accounts/onboarding.html", {"form": form})
