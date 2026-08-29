import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Plan
from .providers import (
    MercadoPagoProvider,
    PaymentProviderConfigurationError,
    PaymentProviderError,
)
from .services import (
    SubscriptionConflictError,
    current_subscription,
    process_mercado_pago_webhook,
    start_subscription,
)


def plans(request):
    active_plans = Plan.objects.filter(is_active=True)
    subscription = current_subscription(request.user) if request.user.is_authenticated else None
    return render(
        request,
        "subscriptions/plans.html",
        {
            "plans": active_plans,
            "current_subscription": subscription,
            "payments_enabled": bool(settings.MERCADO_PAGO_ACCESS_TOKEN),
        },
    )


@require_POST
@login_required
def subscribe(request, slug):
    if not request.user.onboarding_completed:
        messages.info(request, "Complete seu cadastro antes de escolher um plano.")
        return redirect("accounts:onboarding")
    plan = get_object_or_404(Plan, slug=slug, is_active=True)
    if not plan.is_free and not plan.mercado_pago_plan_id:
        messages.info(request, "Este plano ainda está em configuração e não pode ser cobrado.")
        return redirect("subscriptions:plans")
    return_url = f"{settings.PUBLIC_BASE_URL}{reverse('subscriptions:status')}"
    try:
        subscription = start_subscription(
            user=request.user, plan=plan, return_url=return_url, request=request
        )
    except PaymentProviderConfigurationError as exc:
        messages.info(request, str(exc))
        return redirect("subscriptions:plans")
    except PaymentProviderError as exc:
        messages.error(request, str(exc))
        return redirect("subscriptions:plans")
    except SubscriptionConflictError as exc:
        messages.info(request, str(exc))
        return redirect("subscriptions:status")
    if subscription.checkout_url:
        return redirect(subscription.checkout_url)
    messages.success(request, f"Plano {plan.name} ativado com sucesso.")
    return redirect("subscriptions:status")


@login_required
def subscription_status(request):
    return render(
        request,
        "subscriptions/status.html",
        {"subscription": current_subscription(request.user)},
    )


@csrf_exempt
@require_POST
def mercado_pago_webhook(request):
    try:
        payload = json.loads(request.body or b"{}")
    except json.JSONDecodeError:
        return HttpResponseBadRequest("invalid json")
    data_id = request.GET.get("data.id") or payload.get("data", {}).get("id")
    event_id = str(payload.get("id") or f"{payload.get('action', 'event')}:{data_id}")
    provider = MercadoPagoProvider()
    try:
        valid = provider.validate_webhook(
            request.headers.get("x-signature"),
            request.headers.get("x-request-id"),
            data_id,
        )
    except PaymentProviderConfigurationError:
        return HttpResponse(status=503)
    if not valid:
        return HttpResponseForbidden("invalid signature")
    try:
        process_mercado_pago_webhook(
            payload=payload, data_id=data_id, event_id=event_id, provider=provider
        )
    except PaymentProviderError:
        return HttpResponse(status=503)
    return HttpResponse(status=200)
