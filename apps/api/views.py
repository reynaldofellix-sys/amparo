from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from apps.subscriptions.services import current_subscription

from .auth import api_login_required


@require_GET
def health(request):
    return JsonResponse({"api": "v1", "status": "ok"})


@require_GET
@never_cache
@api_login_required
def me(request):
    user = request.user
    subscription = current_subscription(user)
    return JsonResponse(
        {
            "id": str(user.pk),
            "full_name": user.full_name,
            "email": user.email,
            "age_group": user.age_group,
            "accessibility": {"large_text": user.large_text},
            "onboarding_completed": user.onboarding_completed,
            "subscription": (
                {
                    "plan": subscription.plan.slug,
                    "status": subscription.status,
                }
                if subscription
                else None
            ),
        }
    )


@require_GET
@never_cache
@api_login_required
def account_summary(request):
    account = request.user.financial_account
    return JsonResponse(
        {
            "id": str(account.pk),
            "branch": account.branch,
            "number": account.number,
            "currency": account.currency,
            "balance": str(account.balance),
            "status": account.status,
            "demo": True,
        }
    )


@require_GET
@never_cache
@api_login_required
def movements(request):
    entries = request.user.financial_account.ledger_entries.all()[:20]
    return JsonResponse(
        {
            "results": [
                {
                    "id": str(entry.pk),
                    "direction": entry.direction,
                    "amount": str(entry.amount),
                    "description": entry.description,
                    "balance_after": str(entry.balance_after),
                    "occurred_at": entry.occurred_at.isoformat(),
                }
                for entry in entries
            ]
        }
    )
