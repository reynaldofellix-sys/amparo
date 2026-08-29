import logging

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(autoretry_for=(Exception,), retry_backoff=True, retry_kwargs={"max_retries": 5})
def record_transfer_notification(transfer_id):
    from apps.banking.models import Transfer
    from apps.core.services import audit

    transfer = Transfer.objects.select_related("account__owner").get(pk=transfer_id)
    audit(
        event_type="notification.transfer_recorded",
        actor=transfer.account.owner,
        obj=transfer,
        metadata={"channel": "pending-provider-integration"},
    )
    logger.info("Notificação demonstrativa registrada para a transferência %s", transfer_id)
