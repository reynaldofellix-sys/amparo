import logging

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.core.services import audit

from .models import FinancialAccount, LedgerEntry, Transfer

logger = logging.getLogger(__name__)


def enqueue_transfer_notification(transfer_id):
    try:
        from .tasks import record_transfer_notification

        record_transfer_notification.delay(str(transfer_id))
    except Exception:
        logger.exception(
            "Não foi possível enfileirar a notificação da transferência %s", transfer_id
        )


@transaction.atomic
def credit_account(*, account, amount, description, reference, metadata=None):
    locked = FinancialAccount.objects.select_for_update().get(pk=account.pk)
    if amount <= 0:
        raise ValidationError("O crédito deve ser positivo.")
    locked.balance += amount
    locked.save(update_fields=["balance", "updated_at"])
    return LedgerEntry.objects.create(
        account=locked,
        direction=LedgerEntry.Direction.CREDIT,
        amount=amount,
        balance_after=locked.balance,
        description=description,
        reference=reference,
        metadata=metadata or {},
    )


def create_transfer_draft(*, account, recipient_name, pix_key, amount, idempotency_key):
    if account.status != FinancialAccount.Status.ACTIVE:
        raise PermissionDenied("A conta não está disponível para transferências.")
    try:
        transfer, _ = Transfer.objects.get_or_create(
            idempotency_key=idempotency_key,
            defaults={
                "account": account,
                "recipient_name": recipient_name,
                "pix_key": pix_key,
                "amount": amount,
            },
        )
    except IntegrityError:
        transfer = Transfer.objects.get(idempotency_key=idempotency_key)
    if transfer.account_id != account.id:
        raise PermissionDenied("Esta solicitação não pertence à conta autenticada.")
    if (
        transfer.recipient_name != recipient_name
        or transfer.pix_key != pix_key
        or transfer.amount != amount
    ):
        raise ValidationError("A chave de idempotência já foi usada com dados diferentes.")
    return transfer


@transaction.atomic
def complete_transfer(*, transfer_id, user, request=None):
    transfer = (
        Transfer.objects.select_for_update()
        .select_related("account")
        .get(pk=transfer_id, account__owner=user)
    )
    if transfer.status == Transfer.Status.COMPLETED:
        return transfer
    if transfer.status != Transfer.Status.PENDING:
        raise ValidationError("A transferência não pode mais ser concluída.")

    account = FinancialAccount.objects.select_for_update().get(pk=transfer.account_id)
    if account.status != FinancialAccount.Status.ACTIVE:
        raise PermissionDenied("A conta não está ativa.")
    if account.balance < transfer.amount:
        raise ValidationError("Saldo insuficiente para concluir a demonstração.")

    account.balance -= transfer.amount
    account.save(update_fields=["balance", "updated_at"])
    LedgerEntry.objects.create(
        account=account,
        direction=LedgerEntry.Direction.DEBIT,
        amount=transfer.amount,
        balance_after=account.balance,
        description=f"Pix demonstrativo para {transfer.recipient_name}",
        reference=f"transfer:{transfer.idempotency_key}",
        metadata={"transfer_id": str(transfer.id)},
    )
    transfer.status = Transfer.Status.COMPLETED
    transfer.completed_at = timezone.now()
    transfer.save(update_fields=["status", "completed_at", "updated_at"])
    audit(
        event_type="transfer.completed",
        actor=user,
        request=request,
        obj=transfer,
        metadata={"amount": str(transfer.amount)},
    )
    if settings.ASYNC_NOTIFICATIONS_ENABLED:
        transaction.on_commit(lambda: enqueue_transfer_notification(transfer.id))
    return transfer


@transaction.atomic
def cancel_transfer(*, transfer_id, user, request=None):
    transfer = Transfer.objects.select_for_update().get(pk=transfer_id, account__owner=user)
    if transfer.status == Transfer.Status.PENDING:
        transfer.status = Transfer.Status.CANCELLED
        transfer.save(update_fields=["status", "updated_at"])
        audit(event_type="transfer.cancelled", actor=user, request=request, obj=transfer)
    return transfer
