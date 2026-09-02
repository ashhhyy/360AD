from django.core.validators import MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0002_quotationitemextracost"),
    ]

    operations = [
        migrations.AddField(
            model_name="quotationitem",
            name="selling_price_override",
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                help_text="Optional final selling price before VAT.",
                max_digits=14,
                null=True,
                validators=[MinValueValidator(0)],
            ),
        ),
    ]
