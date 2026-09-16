from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction

from .models import Product, ProductCostComponent, QuotationCostSnapshot


MONEY = Decimal("0.01")


def money(value):
    return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)


def calculate_quick_item(
    product,
    *,
    customer_type,
    width=Decimal("0"),
    height=Decimal("0"),
    unit="FT",
    quantity=Decimal("1"),
    other_charges=Decimal("0"),
    discount=Decimal("0"),
    selling_price_override=None,
    extra_cost=Decimal("0"),
):
    """Calculate a quotation line without creating any database record."""
    if product.pricing_type == Product.PricingType.AREA:
        area_per_piece = width * height
        if unit == "IN":
            area_per_piece = area_per_piece / Decimal("144")
        pricing_quantity = area_per_piece * quantity
    else:
        area_per_piece = Decimal("0")
        pricing_quantity = quantity

    breakdown = []
    production_subtotal = Decimal("0")
    for component in product.cost_components.select_related("cost_item").all():
        if component.basis == ProductCostComponent.Basis.AREA:
            computed_quantity = area_per_piece * quantity
            basis_label = "Area × quantity"
        elif component.basis == ProductCostComponent.Basis.PIECE:
            computed_quantity = quantity
            basis_label = "Quantity"
        else:
            computed_quantity = Decimal("1")
            basis_label = "Fixed per job"

        total = money(component.cost_item.unit_cost * component.usage_quantity * computed_quantity)
        production_subtotal += total
        breakdown.append(
            {
                "name": component.cost_item.name,
                "basis": basis_label,
                "consumed": component.usage_quantity * computed_quantity,
                "unit": component.cost_item.consumption_unit,
                "total": total,
            }
        )

    buffer_amount = money(production_subtotal * product.buffer_percent / Decimal("100"))
    if buffer_amount:
        breakdown.append(
            {
                "name": f"Production buffer ({product.buffer_percent}%)",
                "basis": "Percentage of itemized costs",
                "consumed": Decimal("0"),
                "unit": "cost only",
                "total": buffer_amount,
            }
        )
    if extra_cost:
        breakdown.append(
            {
                "name": "Extra production cost",
                "basis": "Quick estimate adjustment",
                "consumed": Decimal("0"),
                "unit": "cost only",
                "total": money(extra_cost),
            }
        )

    total_cost = money(production_subtotal + buffer_amount + extra_cost)
    selling_rate = product.tie_up_rate if customer_type == "TIE_UP" else product.walk_in_rate
    if selling_price_override is not None:
        selling_total = max(money(selling_price_override), Decimal("0"))
    else:
        calculated_selling = money(pricing_quantity * selling_rate + other_charges - discount)
        selling_total = max(money(product.minimum_price), calculated_selling, Decimal("0"))
    gross_profit = money(selling_total - total_cost)
    gp_margin = gross_profit / selling_total * Decimal("100") if selling_total else Decimal("0")

    return {
        "product": product,
        "area_per_piece": area_per_piece,
        "pricing_quantity": pricing_quantity,
        "selling_rate": selling_rate,
        "cost_total": total_cost,
        "selling_total": selling_total,
        "gross_profit": gross_profit,
        "gp_margin": gp_margin,
        "breakdown": breakdown,
    }


@transaction.atomic
def recalculate_quotation_item(item):
    item.cost_breakdown.all().delete()
    snapshots = []
    subtotal = Decimal("0")

    for component in item.product.cost_components.select_related("cost_item").all():
        if component.basis == ProductCostComponent.Basis.AREA:
            computed_quantity = item.area_per_piece * item.quantity
            basis_label = "Area × quantity"
        elif component.basis == ProductCostComponent.Basis.PIECE:
            computed_quantity = item.quantity
            basis_label = "Quantity"
        else:
            computed_quantity = Decimal("1")
            basis_label = "Fixed per job"

        line_total = money(component.cost_item.unit_cost * component.usage_quantity * computed_quantity)
        subtotal += line_total
        snapshots.append(
            QuotationCostSnapshot(
                quotation_item=item,
                name=component.cost_item.name,
                category=component.cost_item.get_category_display(),
                basis=basis_label,
                unit_label=component.cost_item.consumption_unit,
                unit_cost=component.cost_item.unit_cost,
                usage_quantity=component.usage_quantity,
                computed_quantity=computed_quantity,
                total_cost=line_total,
                sequence=component.sequence,
            )
        )

    for index, extra in enumerate(item.extra_costs.select_related("cost_item").all(), start=1):
        if extra.basis == ProductCostComponent.Basis.AREA:
            computed_quantity = item.area_per_piece * item.quantity
            basis_label = "Job-specific: area × quantity"
        elif extra.basis == ProductCostComponent.Basis.PIECE:
            computed_quantity = item.quantity
            basis_label = "Job-specific: quantity"
        else:
            computed_quantity = Decimal("1")
            basis_label = "Job-specific: fixed usage"
        line_total = money(extra.cost_item.unit_cost * extra.usage_quantity * computed_quantity)
        subtotal += line_total
        snapshots.append(
            QuotationCostSnapshot(
                quotation_item=item,
                name=extra.cost_item.name,
                category=extra.cost_item.get_category_display(),
                basis=basis_label,
                unit_label=extra.cost_item.consumption_unit,
                unit_cost=extra.cost_item.unit_cost,
                usage_quantity=extra.usage_quantity,
                computed_quantity=computed_quantity,
                total_cost=line_total,
                sequence=900 + index,
            )
        )

    buffer_amount = money(subtotal * item.product.buffer_percent / Decimal("100"))
    if buffer_amount:
        snapshots.append(
            QuotationCostSnapshot(
                quotation_item=item,
                name=f"Production buffer ({item.product.buffer_percent}%)",
                category="Buffer / Overhead",
                basis="Percentage of itemized costs",
                unit_label="cost only",
                unit_cost=item.product.buffer_percent,
                usage_quantity=Decimal("1"),
                computed_quantity=subtotal,
                total_cost=buffer_amount,
                sequence=999,
            )
        )

    QuotationCostSnapshot.objects.bulk_create(snapshots)
    total_cost = money(subtotal + buffer_amount)
    if item.selling_price_override is not None:
        selling_total = max(money(item.selling_price_override), Decimal("0.00"))
    else:
        calculated_selling = money(item.pricing_quantity * item.selling_rate + item.other_charges - item.discount)
        selling_total = max(money(item.product.minimum_price), calculated_selling, Decimal("0.00"))
    type(item).objects.filter(pk=item.pk).update(cost_total=total_cost, selling_total=selling_total)
    item.cost_total = total_cost
    item.selling_total = selling_total
    return item
