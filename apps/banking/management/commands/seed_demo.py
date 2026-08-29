from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.accounts.models import User
from apps.banking.models import LedgerEntry
from apps.banking.services import credit_account


class Command(BaseCommand):
    help = "Cria uma conta local de demonstração com saldo e movimentações iniciais."

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            email="demo@amparo.local",
            defaults={
                "full_name": "Maria Amparo",
                "phone": "(88) 99999-0000",
                "age_group": "senior",
            },
        )
        if created:
            user.set_password("AmparoDemo2026!")
            user.save(update_fields=["password"])
        account = user.financial_account
        entries = [
            (Decimal("600.00"), "Benefício demonstrativo", "demo:benefit:1"),
            (Decimal("650.00"), "Saldo inicial demonstrativo", "demo:opening:1"),
        ]
        for amount, description, reference in entries:
            if not LedgerEntry.objects.filter(account=account, reference=reference).exists():
                credit_account(
                    account=account,
                    amount=amount,
                    description=description,
                    reference=reference,
                    metadata={"demo": True},
                )
        self.stdout.write(
            self.style.SUCCESS("Conta demo pronta: demo@amparo.local / AmparoDemo2026!")
        )
