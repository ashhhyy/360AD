from decimal import Decimal, InvalidOperation

from django import forms

from .models import Client, CostItem, Product, ProductCostComponent, Quotation, QuotationItem, QuotationItemExtraCost


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
