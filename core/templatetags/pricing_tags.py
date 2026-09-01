from decimal import Decimal, InvalidOperation

from django import template


register = template.Library()


@register.filter
def subtract(value, arg):
    try:
        return value - arg
    except (TypeError, ValueError):
        return ""


@register.filter
def number2(value):
    """Display numeric values with commas and exactly two decimal places."""
    if value is None or value == "":
        return ""
    try:
        return f"{Decimal(str(value)):,.2f}"
    except (InvalidOperation, TypeError, ValueError):
        return value
