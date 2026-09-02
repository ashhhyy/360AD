from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_quotationitem_selling_price_override"),
    ]

    operations = [
        migrations.CreateModel(
            name="QuotationSequence",
            fields=[
                ("year", models.PositiveIntegerField(primary_key=True, serialize=False)),
                ("next_number", models.PositiveIntegerField(default=1)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["year"]},
        ),
    ]
