from django.db import migrations, models


def backfill_reusable_2026_gaps(apps, schema_editor):
    Quotation = apps.get_model("core", "Quotation")
    QuotationSequence = apps.get_model("core", "QuotationSequence")
    ReusableQuotationNumber = apps.get_model("core", "ReusableQuotationNumber")
    sequence = QuotationSequence.objects.filter(year=2026).first()
    if sequence is None:
        return

    existing_numbers = set()
    for quote_number in Quotation.objects.filter(quote_number__startswith="360AD-2026-").values_list(
        "quote_number", flat=True
    ):
        try:
            existing_numbers.add(int(quote_number.rsplit("-", 1)[1]))
        except (IndexError, TypeError, ValueError):
            continue

    reusable = [
        ReusableQuotationNumber(year=2026, number=number)
        for number in range(55, max(sequence.next_number, 55))
        if number not in existing_numbers
    ]
    ReusableQuotationNumber.objects.bulk_create(reusable, ignore_conflicts=True)


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_project_cost_summary"),
    ]

    operations = [
        migrations.AlterField(
            model_name="quotation",
            name="status",
            field=models.CharField(
                choices=[
                    ("DRAFT", "Draft"),
                    ("TEST", "Test"),
                    ("APPROVED", "Approved"),
                    ("SENT", "Sent"),
                    ("ACCEPTED", "Accepted"),
                    ("REJECTED", "Rejected"),
                    ("EXPIRED", "Expired"),
                ],
                default="DRAFT",
                max_length=12,
            ),
        ),
        migrations.CreateModel(
            name="ReusableQuotationNumber",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("year", models.PositiveIntegerField()),
                ("number", models.PositiveIntegerField()),
                ("released_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["year", "number"]},
        ),
        migrations.AddConstraint(
            model_name="reusablequotationnumber",
            constraint=models.UniqueConstraint(
                fields=("year", "number"),
                name="unique_reusable_quotation_number",
            ),
        ),
        migrations.RunPython(backfill_reusable_2026_gaps, migrations.RunPython.noop),
    ]
