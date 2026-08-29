from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.urls import reverse


class AmparoAccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        if request.user.is_authenticated and not request.user.onboarding_completed:
            return reverse("accounts:onboarding")
        return reverse("dashboard")


class AmparoSocialAccountAdapter(DefaultSocialAccountAdapter):
    def new_user(self, request, sociallogin):
        user = super().new_user(request, sociallogin)
        user.onboarding_completed = False
        user.set_unusable_password()
        return user

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)
        user.email = (data.get("email") or "").strip().lower()
        user.full_name = (data.get("name") or "").strip()
        user.onboarding_completed = False
        return user
