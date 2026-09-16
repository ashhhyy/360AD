from django.db import migrations, models


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
    ]
