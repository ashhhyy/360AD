from django.contrib import admin

from .models import Client, CostItem, Product, ProductCostComponent, Quotation, QuotationCostSnapshot, QuotationItem, QuotationItemExtraCost


class ProductCostComponentInline(admin.TabularInline):
    model = ProductCostComponent
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "pricing_type", "walk_in_rate", "tie_up_rate", "buffer_percent", "active")
    list_filter = ("pricing_type", "active")
    search_fields = ("name",)
    inlines = [ProductCostComponentInline]


@admin.register(CostItem)
class CostItemAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "unit", "unit_cost", "supplier", "active")
    list_filter = ("category", "unit", "active")
    search_fields = ("name", "supplier")


admin.site.register(Client)
admin.site.register(Quotation)
admin.site.register(QuotationItem)
admin.site.register(QuotationItemExtraCost)
admin.site.register(QuotationCostSnapshot)

admin.site.site_header = "360 A.D System Administration"
admin.site.site_title = "360 A.D Admin"
