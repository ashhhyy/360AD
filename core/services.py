from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction

from .models import ProductCostComponent, QuotationCostSnapshot


MONEY = Decimal("0.01")


def money(value):
    return Decimal(value).quantize(MONEY, rounding=ROUND_HALF_UP)


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
