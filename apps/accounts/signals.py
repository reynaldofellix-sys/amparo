from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.banking.models import FinancialAccount

from .models import User


@receiver(post_save, sender=User)
def create_financial_account(sender, instance, created, **kwargs):
    if created:
        FinancialAccount.objects.create(owner=instance)
