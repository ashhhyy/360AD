from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Sum
from django.utils import timezone


ZERO = Decimal("0.00")


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Client(TimeStampedModel):
    name = models.CharField(max_length=160)
    company = models.CharField(max_length=160, blank=True)
    contact_number = models.CharField(max_length=80, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    tax_id = models.CharField("TIN", max_length=80, blank=True)
    notes = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.company or self.name


class CostItem(TimeStampedModel):
    class Category(models.TextChoices):
        MATERIAL = "MATERIAL", "Material"
        LAMINATE = "LAMINATE", "Laminate"
        BOARD = "BOARD", "Board / Substrate"
        INK = "INK", "Ink"
        ELECTRICITY = "ELECTRICITY", "Electricity"
        MANPOWER = "MANPOWER", "Manpower"
        MACHINE = "MACHINE", "Machine"
        FINISHING = "FINISHING", "Finishing / Consumable"
        INSTALLATION = "INSTALLATION", "Installation"
        PACKAGING = "PACKAGING", "Packaging"
        OTHER = "OTHER", "Other"

    class Unit(models.TextChoices):
        SQFT = "SQFT", "per sq.ft."
        PIECE = "PIECE", "per piece"
        HOUR = "HOUR", "per hour"
        MINUTE = "MINUTE", "per minute"
        JOB = "JOB", "per job / setup"
        UNIT = "UNIT", "per unit"

    name = models.CharField(max_length=180, unique=True)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.MATERIAL)
    supplier = models.CharField(max_length=160, blank=True)
    unit = models.CharField(max_length=10, choices=Unit.choices, default=Unit.SQFT)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=4, validators=[MinValueValidator(0)])
    vat_inclusive = models.BooleanField(default=True)
    purchase_description = models.CharField(max_length=220, blank=True)
    notes = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category", "name"]

    @property
    def consumption_unit(self):
        return {
            self.Unit.SQFT: "sq.ft.",
            self.Unit.PIECE: "piece",
            self.Unit.HOUR: "hour",
            self.Unit.MINUTE: "minute",
            self.Unit.JOB: "job / setup",
            self.Unit.UNIT: "unit",
        }.get(self.unit, "unit")

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    class PricingType(models.TextChoices):
        AREA = "AREA", "Area-based"
        PIECE = "PIECE", "Piece-based"

    name = models.CharField(max_length=180, unique=True)
    pricing_type = models.CharField(max_length=10, choices=PricingType.choices)
    walk_in_rate = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])
    tie_up_rate = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])
    minimum_price = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    buffer_percent = models.DecimalField(max_digits=6, decimal_places=2, default=5, validators=[MinValueValidator(0)])
    notes = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    @property
    def pricing_basis(self):
        return "per sq.ft." if self.pricing_type == self.PricingType.AREA else "per piece"

    def __str__(self):
        return self.name


class ProductCostComponent(TimeStampedModel):
    class Basis(models.TextChoices):
        AREA = "AREA", "Area × quantity"
        PIECE = "PIECE", "Quantity"
        FIXED = "FIXED", "Fixed per job"

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="cost_components")
    cost_item = models.ForeignKey(CostItem, on_delete=models.PROTECT, related_name="product_components")
    basis = models.CharField(max_length=10, choices=Basis.choices)
    usage_quantity = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=1,
        validators=[MinValueValidator(Decimal("0.0001"))],
        help_text="Amount of this cost item used for each sq.ft., piece, or job.",
    )
    sequence = models.PositiveIntegerField(default=10)
    notes = models.CharField(max_length=220, blank=True)

    class Meta:
        ordering = ["sequence", "id"]
        constraints = [
            models.UniqueConstraint(fields=["product", "cost_item", "basis"], name="unique_product_cost_basis")
        ]

    def __str__(self):
        return f"{self.product} – {self.cost_item}"


class QuotationSequence(models.Model):
    year = models.PositiveIntegerField(primary_key=True)
    next_number = models.PositiveIntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["year"]

    def __str__(self):
        return f"{self.year}: next {self.next_number:05d}"


class Quotation(TimeStampedModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        APPROVED = "APPROVED", "Approved"
        SENT = "SENT", "Sent"
        ACCEPTED = "ACCEPTED", "Accepted"
        REJECTED = "REJECTED", "Rejected"
        EXPIRED = "EXPIRED", "Expired"

    class CustomerType(models.TextChoices):
        WALK_IN = "WALK_IN", "Walk-In"
        TIE_UP = "TIE_UP", "Tie-Up"

    quote_number = models.CharField(max_length=40, unique=True, blank=True)
    client = models.ForeignKey(Client, on_delete=models.PROTECT, related_name="quotations")
    project_name = models.CharField(max_length=180, blank=True)
    customer_type = models.CharField(max_length=10, choices=CustomerType.choices, default=CustomerType.WALK_IN)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    quotation_date = models.DateField(default=timezone.localdate)
    validity_days = models.PositiveIntegerField(default=15)
    vat_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey("auth.User", on_delete=models.PROTECT, related_name="quotations")

    class Meta:
        ordering = ["-created_at"]

    @classmethod
    def _configured_start_number(cls, year):
        if year == settings.QUOTE_SEQUENCE_START_YEAR:
            return settings.QUOTE_SEQUENCE_START_NUMBER
        return 1

    @classmethod
    def _allocate_number(cls, year):
        configured_start = cls._configured_start_number(year)
        sequence, created = QuotationSequence.objects.select_for_update().get_or_create(
            year=year,
            defaults={"next_number": configured_start},
        )
        next_number = sequence.next_number

        if created:
            prefix = f"360AD-{year}-"
            existing_numbers = []
            for quote_number in cls.objects.filter(quote_number__startswith=prefix).values_list(
                "quote_number", flat=True
            ):
                try:
                    existing_numbers.append(int(quote_number.rsplit("-", 1)[1]))
                except (IndexError, TypeError, ValueError):
                    continue
            if existing_numbers:
                next_number = max(configured_start, max(existing_numbers) + 1)

        sequence.next_number = next_number + 1
        sequence.save(update_fields=["next_number", "updated_at"])
        return next_number

    def save(self, *args, **kwargs):
        if self.quote_number:
            return super().save(*args, **kwargs)

        with transaction.atomic():
            sequence_number = self._allocate_number(self.quotation_date.year)
            self.quote_number = f"360AD-{self.quotation_date.year}-{sequence_number:05d}"
            return super().save(*args, **kwargs)

    @property
    def item_cost_total(self):
        return self.items.aggregate(total=Sum("cost_total"))["total"] or ZERO

    @property
    def additional_cost_total(self):
        return self.additional_costs.aggregate(total=Sum("amount"))["total"] or ZERO

    @property
    def total_cost(self):
        return self.item_cost_total + self.additional_cost_total

    @property
    def subtotal(self):
        return self.items.aggregate(total=Sum("selling_total"))["total"] or ZERO

    @property
    def vat_amount(self):
        return (self.subtotal * self.vat_percent / Decimal("100")).quantize(Decimal("0.01"))

    @property
    def grand_total(self):
        return self.subtotal + self.vat_amount

    @property
    def gross_profit(self):
        return self.subtotal - self.total_cost

    @property
    def gp_margin(self):
        return (self.gross_profit / self.subtotal * Decimal("100")) if self.subtotal else ZERO

    def __str__(self):
        return self.quote_number or f"Quotation {self.pk}"


class QuotationItem(TimeStampedModel):
    class Unit(models.TextChoices):
        FEET = "FT", "feet"
        INCHES = "IN", "inches"

    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="quotation_items")
    description = models.CharField(max_length=240, blank=True)
    width = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True, validators=[MinValueValidator(0)])
    height = models.DecimalField(max_digits=12, decimal_places=3, null=True, blank=True, validators=[MinValueValidator(0)])
    unit = models.CharField(max_length=2, choices=Unit.choices, default=Unit.FEET)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=1, validators=[MinValueValidator(Decimal("0.01"))])
    selling_rate = models.DecimalField(max_digits=14, decimal_places=2, validators=[MinValueValidator(0)])
    selling_price_override = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Optional final selling price before VAT.",
    )
    other_charges = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    discount = models.DecimalField(max_digits=14, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    cost_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    selling_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        ordering = ["id"]

    @property
    def area_per_piece(self):
        if self.product.pricing_type != Product.PricingType.AREA or self.width is None or self.height is None:
            return ZERO
        area = self.width * self.height
        if self.unit == self.Unit.INCHES:
            area = area / Decimal("144")
        return area

    @property
    def pricing_quantity(self):
        if self.product.pricing_type == Product.PricingType.AREA:
            return self.area_per_piece * self.quantity
        return self.quantity

    def __str__(self):
        return f"{self.quotation} – {self.product}"


class QuotationItemExtraCost(TimeStampedModel):
    quotation_item = models.ForeignKey(QuotationItem, on_delete=models.CASCADE, related_name="extra_costs")
    cost_item = models.ForeignKey(CostItem, on_delete=models.PROTECT, related_name="quotation_extra_costs")
    basis = models.CharField(max_length=10, choices=ProductCostComponent.Basis.choices, default=ProductCostComponent.Basis.FIXED)
    usage_quantity = models.DecimalField(
        max_digits=14,
        decimal_places=4,
        default=1,
        validators=[MinValueValidator(Decimal("0.0001"))],
        help_text="Example: enter 4 for four eyelets, or 3 for three installation hours.",
    )
    notes = models.CharField(max_length=220, blank=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.quotation_item} – {self.cost_item}"


class QuotationAdditionalCost(TimeStampedModel):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name="additional_costs")
    name = models.CharField(max_length=180)
    category = models.CharField(max_length=20, choices=CostItem.Category.choices, default=CostItem.Category.OTHER)
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    notes = models.CharField(max_length=240, blank=True)
    created_by = models.ForeignKey(
        "auth.User",
        on_delete=models.PROTECT,
        related_name="quotation_additional_costs",
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.quotation} – {self.name}"


class QuotationCostSnapshot(models.Model):
    quotation_item = models.ForeignKey(QuotationItem, on_delete=models.CASCADE, related_name="cost_breakdown")
    name = models.CharField(max_length=180)
    category = models.CharField(max_length=30)
    basis = models.CharField(max_length=40)
    unit_label = models.CharField(max_length=30, blank=True)
    unit_cost = models.DecimalField(max_digits=14, decimal_places=4)
    usage_quantity = models.DecimalField(max_digits=14, decimal_places=4)
    computed_quantity = models.DecimalField(max_digits=14, decimal_places=4)
    total_cost = models.DecimalField(max_digits=14, decimal_places=2)
    sequence = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ["sequence", "id"]

    def __str__(self):
        return f"{self.quotation_item}: {self.name}"

    @property
    def consumed_quantity(self):
        return self.usage_quantity * self.computed_quantity
