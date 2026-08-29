from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import User


class RegistrationForm(UserCreationForm):
    consent = forms.BooleanField(
        label="Li e aceito os termos da demonstração e o aviso de privacidade."
    )

    class Meta:
        model = User
        fields = ("full_name", "email", "phone", "age_group")
        widgets = {
            "full_name": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email", "inputmode": "email"}),
            "phone": forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel"}),
        }

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class EmailAuthenticationForm(forms.Form):
    email = forms.EmailField(
        label="E-mail",
        widget=forms.EmailInput(attrs={"autocomplete": "username", "inputmode": "email"}),
    )
    password = forms.CharField(
        label="Senha",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get("email")
        password = cleaned.get("password")
        if email and password:
            self.user_cache = authenticate(
                self.request, username=email.strip().lower(), password=password
            )
            if self.user_cache is None:
                raise forms.ValidationError("E-mail ou senha inválidos.")
            if not self.user_cache.is_active:
                raise forms.ValidationError("Esta conta está desativada.")
        return cleaned

    def get_user(self):
        return self.user_cache


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("full_name", "email", "phone", "age_group", "large_text")
        widgets = {
            "full_name": forms.TextInput(attrs={"autocomplete": "name"}),
            "email": forms.EmailInput(attrs={"autocomplete": "email", "inputmode": "email"}),
            "phone": forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel"}),
        }

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()


class SecurityPreferencesForm(forms.ModelForm):
    class Meta:
        model = User
        fields = (
            "transfer_alerts",
            "login_alerts",
            "security_alerts",
            "confirm_transfers",
            "large_text",
        )
        labels = {
            "transfer_alerts": "Alertas de transferência",
            "login_alerts": "Alertas de acesso",
            "security_alerts": "Alertas de segurança",
            "confirm_transfers": "Confirmar transferências",
            "large_text": "Texto ampliado",
        }


class SocialOnboardingForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Criar uma senha (opcional)",
        required=False,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
        help_text="Você poderá entrar pelo Google mesmo sem criar uma senha.",
    )
    password2 = forms.CharField(
        label="Confirmar a senha",
        required=False,
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    consent = forms.BooleanField(
        label="Li e aceito os termos da demonstração e o aviso de privacidade."
    )

    class Meta:
        model = User
        fields = ("full_name", "phone", "age_group", "large_text")
        widgets = {
            "full_name": forms.TextInput(attrs={"autocomplete": "name"}),
            "phone": forms.TextInput(attrs={"autocomplete": "tel", "inputmode": "tel"}),
        }

    def clean(self):
        cleaned = super().clean()
        password1 = cleaned.get("password1")
        password2 = cleaned.get("password2")
        if password1 or password2:
            if password1 != password2:
                self.add_error("password2", "As senhas não coincidem.")
            elif password1:
                try:
                    validate_password(password1, self.instance)
                except ValidationError as exc:
                    self.add_error("password1", exc)
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password1")
        if password:
            user.set_password(password)
        elif not user.has_usable_password():
            user.set_unusable_password()
        user.onboarding_completed = True
        if commit:
            user.save()
        return user
