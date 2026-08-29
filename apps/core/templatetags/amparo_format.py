from decimal import Decimal

from django import template

register = template.Library()


@register.filter
def brl(value):
    try:
        number = Decimal(value)
    except (TypeError, ValueError):
        number = Decimal("0")
    formatted = f"{number:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"R$ {formatted}"
