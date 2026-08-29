from decimal import Decimal

from django.db import migrations


PLANS = (
    {
        "slug": "gratuito",
        "name": "Gratuito",
        "description": "Para conhecer o AMPARO e organizar sua rotina financeira com calma.",
        "price": Decimal("0.00"),
        "features": [
            "Conta demonstrativa",
            "Movimentações e Pix educativo",
            "Assistente de segurança",
            "Recursos de acessibilidade",
        ],
        "sort_order": 10,
    },
    {
        "slug": "cuidado",
        "name": "Cuidado",
        "description": "Mais orientação e acompanhamento para usar o serviço com confiança.",
        "price": Decimal("14.90"),
        "features": [
            "Tudo do plano Gratuito",
            "Alertas personalizados",
            "Conteúdos educativos ampliados",
            "Prioridade em novos recursos",
        ],
        "is_recommended": True,
        "sort_order": 20,
    },
    {
        "slug": "familia",
        "name": "Família",
        "description": "Estrutura preparada para acompanhamento autorizado por familiares.",
        "price": Decimal("29.90"),
        "features": [
            "Tudo do plano Cuidado",
            "Até três acompanhantes autorizados",
            "Resumo familiar de segurança",
            "Controles de privacidade por pessoa",
        ],
        "sort_order": 30,
    },
)


def create_plans(apps, schema_editor):
    Plan = apps.get_model("subscriptions", "Plan")
    for data in PLANS:
        Plan.objects.update_or_create(slug=data["slug"], defaults=data)


def remove_plans(apps, schema_editor):
    Plan = apps.get_model("subscriptions", "Plan")
    Plan.objects.filter(slug__in=[plan["slug"] for plan in PLANS]).delete()


class Migration(migrations.Migration):
    dependencies = [("subscriptions", "0001_initial")]
    operations = [migrations.RunPython(create_plans, remove_plans)]
