from django.http import JsonResponse
from django.shortcuts import redirect


class OnboardingRequiredMiddleware:
    allowed_prefixes = (
        "/autenticacao/",
        "/conta/completar-cadastro/",
        "/conta/sair/",
        "/static/",
        "/health/",
        "/offline/",
        "/service-worker.js",
        "/webhooks/",
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        needs_onboarding = (
            user.is_authenticated
            and not user.onboarding_completed
            and not request.path.startswith(self.allowed_prefixes)
        )
        if needs_onboarding:
            if request.path.startswith("/api/"):
                return JsonResponse(
                    {
                        "detail": "onboarding_required",
                        "onboarding_url": "/conta/completar-cadastro/",
                    },
                    status=409,
                )
            return redirect("accounts:onboarding")
        return self.get_response(request)
