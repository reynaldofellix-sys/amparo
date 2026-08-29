from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.core.services import audit

from .forms import TransferForm
from .models import PaymentCard, Transfer
from .services import cancel_transfer, complete_transfer, create_transfer_draft


@login_required
def dashboard(request):
    account = request.user.financial_account
    recent_entries = account.ledger_entries.all()[:5]
    return render(
        request,
        "banking/dashboard.html",
        {"account": account, "recent_entries": recent_entries},
    )


@login_required
def transactions(request):
    account = request.user.financial_account
    paginator = Paginator(account.ledger_entries.all(), 20)
    page = paginator.get_page(request.GET.get("page"))
    return render(request, "banking/transactions.html", {"account": account, "page": page})


@login_required
def account_detail(request):
    return render(
        request, "banking/account_detail.html", {"account": request.user.financial_account}
    )


@login_required
def card_detail(request):
    card = PaymentCard.objects.filter(account=request.user.financial_account).first()
    return render(request, "banking/card_detail.html", {"card": card})


@require_POST
@login_required
def card_request(request):
    card, created = PaymentCard.objects.get_or_create(account=request.user.financial_account)
    if created:
        audit(event_type="card.requested", actor=request.user, request=request, obj=card)
        messages.success(request, "Solicitação demonstrativa registrada.")
    else:
        messages.info(request, "Sua solicitação demonstrativa já está registrada.")
    return redirect("card-detail")


@login_required
def transfer_create(request):
    form = TransferForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        transfer = create_transfer_draft(
            account=request.user.financial_account,
            recipient_name=form.cleaned_data["recipient_name"],
            pix_key=form.cleaned_data["pix_key"],
            amount=form.cleaned_data["amount"],
            idempotency_key=form.cleaned_data["request_key"],
        )
        return redirect("transfer-review", pk=transfer.pk)
    return render(request, "banking/transfer_form.html", {"form": form})


@login_required
def transfer_review(request, pk):
    transfer = get_object_or_404(Transfer, pk=pk, account__owner=request.user)
    return render(request, "banking/transfer_review.html", {"transfer": transfer})


@require_POST
@login_required
def transfer_confirm(request, pk):
    try:
        transfer = complete_transfer(transfer_id=pk, user=request.user, request=request)
    except (ValidationError, PermissionDenied) as exc:
        messages.error(request, exc.messages[0] if hasattr(exc, "messages") else str(exc))
        return redirect("transfer-review", pk=pk)
    messages.success(request, "Transferência demonstrativa concluída.")
    return redirect("transfer-detail", pk=transfer.pk)


@require_POST
@login_required
def transfer_cancel(request, pk):
    cancel_transfer(transfer_id=pk, user=request.user, request=request)
    messages.info(request, "Transferência cancelada.")
    return redirect("dashboard")


@login_required
def transfer_detail(request, pk):
    transfer = get_object_or_404(Transfer, pk=pk, account__owner=request.user)
    return render(request, "banking/transfer_detail.html", {"transfer": transfer})
