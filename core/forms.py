from decimal import Decimal, InvalidOperation

from django import forms

from .models import (
    Client,
    CostItem,
    Product,
    ProductCostComponent,
    Quotation,
    QuotationAdditionalCost,
    QuotationItem,
    QuotationItemExtraCost,
)


class TwoDecimalNumberInput(forms.NumberInput):
    """Keep forms readable while models retain precise costing calculations."""

    def __init__(self, attrs=None):
        defaults = dict(attrs or {})
        defaults.update({"step": "0.01", "inputmode": "decimal"})
        super().__init__(defaults)

    def format_value(self, value):
        if value is None or value == "":
            return None
        try:
            return f"{Decimal(str(value)):.2f}"
        except (InvalidOperation, TypeError, ValueError):
            return value


class MeasurementNumberInput(forms.NumberInput):
    """Preserve metric precision while keeping simple values readable."""

    def __init__(self, attrs=None):
        defaults = dict(attrs or {})
        defaults.update({"step": "0.0001", "inputmode": "decimal"})
        super().__init__(defaults)

    def format_value(self, value):
        if value is None or value == "":
            return None
        try:
            formatted = f"{Decimal(str(value)):.4f}".rstrip("0").rstrip(".")
            if "." not in formatted:
                return f"{formatted}.00"
            decimals = len(formatted.rsplit(".", 1)[1])
            return formatted + ("0" * max(0, 2 - decimals))
        except (InvalidOperation, TypeError, ValueError):
            return value


class StyledModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs["class"] = "form-check-input"
            else:
                if isinstance(field, forms.DecimalField):
                    field.widget = TwoDecimalNumberInput(attrs=field.widget.attrs)
                field.widget.attrs["class"] = "form-control"


class ClientForm(StyledModelForm):
    class Meta:
        model = Client
        fields = ["name", "company", "contact_number", "email", "address", "tax_id", "notes", "active"]
        widgets = {"address": forms.Textarea(attrs={"rows": 2}), "notes": forms.Textarea(attrs={"rows": 2})}


class CostItemForm(StyledModelForm):
    class Meta:
        model = CostItem
        fields = [
            "name",
            "category",
            "supplier",
            "unit",
            "unit_cost",
            "vat_inclusive",
            "purchase_description",
            "notes",
            "active",
        ]
        widgets = {"notes": forms.Textarea(attrs={"rows": 2})}


class ProductForm(StyledModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "pricing_type",
            "walk_in_rate",
            "tie_up_rate",
            "minimum_price",
            "buffer_percent",
            "notes",
            "active",
        ]
        widgets = {"notes": forms.Textarea(attrs={"rows": 2})}


class ProductCostComponentForm(StyledModelForm):
    class Meta:
        model = ProductCostComponent
        fields = ["cost_item", "basis", "usage_quantity", "sequence", "notes"]


class QuotationForm(StyledModelForm):
    class Meta:
        model = Quotation
        fields = [
            "quote_number",
            "client",
            "project_name",
            "customer_type",
            "status",
            "quotation_date",
            "validity_days",
            "vat_percent",
            "notes",
        ]
        widgets = {
            "quotation_date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["quote_number"].label = "Quotation Number (Optional Override)"
        self.fields["quote_number"].required = False
        self.fields["quote_number"].help_text = (
            "Leave blank on a new quotation to use the next automatic 360AD number. "
            "Enter a different unique number only when an admin override is needed."
        )

    def clean_quote_number(self):
        quote_number = (self.cleaned_data.get("quote_number") or "").strip().upper()
        if not quote_number and self.instance.pk:
            return self.instance.quote_number
        return quote_number


class QuotationItemForm(StyledModelForm):
    class Meta:
        model = QuotationItem
        fields = [
            "product",
            "description",
            "width",
            "height",
            "unit",
            "quantity",
            "selling_rate",
            "selling_price_override",
            "other_charges",
            "discount",
        ]

    def __init__(self, *args, quotation=None, **kwargs):
        self.quotation = quotation
        super().__init__(*args, **kwargs)
        self.fields["selling_rate"].required = False
        self.fields["selling_rate"].help_text = "Leave blank to use the product's Walk-In or Tie-Up rate."
        self.fields["selling_price_override"].label = "Manual Selling Price Override (Before VAT)"
        self.fields["selling_price_override"].help_text = (
            "Optional. When entered, this exact amount becomes the final selling price before VAT "
            "and replaces the automatic rate, other charges, discount, and minimum-price calculation."
        )
        self.fields["unit"].label = "Measurement Unit"
        self.fields["unit"].help_text = (
            "Choose how width and height were measured. All area selling and cost rates remain "
            "uniform and are automatically converted to the per-square-foot basis."
        )
        self.fields["width"].help_text = "Use the selected measurement unit below."
        self.fields["height"].help_text = "Use the selected measurement unit below."
        for field_name in ("width", "height"):
            self.fields[field_name].widget = MeasurementNumberInput(attrs=self.fields[field_name].widget.attrs)
        self.fields["product"].queryset = Product.objects.filter(active=True)

    def clean(self):
        cleaned = super().clean()
        product = cleaned.get("product")
        if product and product.pricing_type == Product.PricingType.AREA:
            if not cleaned.get("width") or not cleaned.get("height"):
                raise forms.ValidationError("Width and height are required for area-based products.")
        if product and not cleaned.get("selling_rate"):
            customer_type = self.quotation.customer_type if self.quotation else Quotation.CustomerType.WALK_IN
            cleaned["selling_rate"] = (
                product.tie_up_rate if customer_type == Quotation.CustomerType.TIE_UP else product.walk_in_rate
            )
        return cleaned


class QuotationItemExtraCostForm(StyledModelForm):
    class Meta:
        model = QuotationItemExtraCost
        fields = ["cost_item", "basis", "usage_quantity", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cost_item"].queryset = CostItem.objects.filter(active=True)


class QuotationAdditionalCostForm(StyledModelForm):
    class Meta:
        model = QuotationAdditionalCost
        fields = ["name", "category", "amount", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].label = "Additional Cost Name"
        self.fields["name"].help_text = "Example: delivery, parking, permit, outsourced labor, or rush expense."
        self.fields["amount"].label = "Cost Amount"
        self.fields["amount"].help_text = "This increases true cost and reduces GP; it is not added to the client selling price."
