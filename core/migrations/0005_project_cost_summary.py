from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


UNIT_LABELS = {
    "SQFT": "sq.ft.",
    "PIECE": "piece",
    "HOUR": "hour",
    "MINUTE": "minute",
    "JOB": "job / setup",
    "UNIT": "unit",
}


def backfill_snapshot_units(apps, schema_editor):
    CostItem = apps.get_model("core", "CostItem")
    QuotationCostSnapshot = apps.get_model("core", "QuotationCostSnapshot")
    units_by_name = dict(CostItem.objects.values_list("name", "unit"))
    snapshots = []
    for snapshot in QuotationCostSnapshot.objects.all().iterator():
        unit_code = units_by_name.get(snapshot.name)
        if unit_code:
            snapshot.unit_label = UNIT_LABELS.get(unit_code, "unit")
        elif "Area" in snapshot.basis or "area" in snapshot.basis:
            snapshot.unit_label = "sq.ft."
        elif "Quantity" in snapshot.basis or "quantity" in snapshot.basis:
            snapshot.unit_label = "piece"
        elif "Percentage" in snapshot.basis:
            snapshot.unit_label = "cost only"
        else:
            snapshot.unit_label = "job / setup"
        snapshots.append(snapshot)
    if snapshots:
        QuotationCostSnapshot.objects.bulk_update(snapshots, ["unit_label"])


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0004_quotationsequence"),
    ]

    operations = [
        migrations.AddField(
            model_name="quotationcostsnapshot",
            name="unit_label",
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.CreateModel(
            name="QuotationAdditionalCost",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("name", models.CharField(max_length=180)),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("MATERIAL", "Material"),
                            ("LAMINATE", "Laminate"),
                            ("BOARD", "Board / Substrate"),
                            ("INK", "Ink"),
                            ("ELECTRICITY", "Electricity"),
                            ("MANPOWER", "Manpower"),
                            ("MACHINE", "Machine"),
                            ("FINISHING", "Finishing / Consumable"),
                            ("INSTALLATION", "Installation"),
                            ("PACKAGING", "Packaging"),
                            ("OTHER", "Other"),
                        ],
                        default="OTHER",
                        max_length=20,
                    ),
                ),
                (
                    "amount",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=14,
                        validators=[django.core.validators.MinValueValidator(Decimal("0.01"))],
                    ),
                ),
                ("notes", models.CharField(blank=True, max_length=240)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="quotation_additional_costs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "quotation",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="additional_costs",
                        to="core.quotation",
                    ),
                ),
            ],
            options={"ordering": ["id"]},
        ),
        migrations.RunPython(backfill_snapshot_units, migrations.RunPython.noop),
    ]
