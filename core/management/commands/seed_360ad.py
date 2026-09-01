from decimal import Decimal

from django.core.management.base import BaseCommand

from core.models import Client, CostItem, Product, ProductCostComponent


class Command(BaseCommand):
    help = "Load the initial 360 A.D materials, product prices, and itemized cost recipes."

    def handle(self, *args, **options):
        def cost(name, category, unit, unit_cost, supplier="", notes=""):
            item, _ = CostItem.objects.update_or_create(
                name=name,
                defaults={
                    "category": category,
                    "unit": unit,
                    "unit_cost": Decimal(str(unit_cost)),
                    "supplier": supplier,
                    "notes": notes,
                    "active": True,
                },
            )
            return item

        C = CostItem.Category
        U = CostItem.Unit
        items = {
            "tarp": cost("Banner 10oz Tarpaulin", C.MATERIAL, U.SQFT, "3.0007", "PTC"),
            "blockout": cost("Blockout Banner 13oz", C.MATERIAL, U.SQFT, "4.1812", "PTC"),
            "panaflex": cost("Panaflex Banner 20oz", C.MATERIAL, U.SQFT, "11.6618", "PTC"),
            "vinyl": cost("White Glossy Vinyl Sticker 120gsm", C.MATERIAL, U.SQFT, "5.2710", "PTC"),
            "hologram": cost("Hologram Sticker", C.MATERIAL, U.SQFT, "5.2710", "Sofie"),
            "laminate": cost("Cold Lamination Glossy", C.LAMINATE, U.SQFT, "3.3972"),
            "sintra15": cost("Sintra Board 1.5mm", C.BOARD, U.SQFT, "9.2188"),
            "sintra3": cost("Sintra Board 3mm", C.BOARD, U.SQFT, "24.0625"),
            "sintra5": cost("Sintra Board 5mm", C.BOARD, U.SQFT, "25.3750"),
            "foam": cost("Foam Board 5mm", C.BOARD, U.SQFT, "9.8000"),
            "acrylic15": cost("Clear Acrylic 1.5mm", C.BOARD, U.SQFT, "42.7000"),
            "acrylic3": cost("Clear Acrylic 3mm", C.BOARD, U.SQFT, "86.1000"),
            "ink": cost("Eco-Solvent Ink", C.INK, U.SQFT, "1.5000"),
            "electricity_area": cost("Electricity – Area Production", C.ELECTRICITY, U.SQFT, "0.1000"),
            "manpower_area": cost("Manpower – Area Production", C.MANPOWER, U.SQFT, "1.5000"),
            "printer": cost("Eco-Solvent Printer", C.MACHINE, U.SQFT, "1.0000"),
            "cutter_area": cost("Cutter Plotter – Area", C.MACHINE, U.SQFT, "1.0000"),
            "eyelet": cost("Eyelet 10mm", C.FINISHING, U.PIECE, "0.5250"),
            "shirt": cost("Blank Shirt", C.MATERIAL, U.PIECE, "120.0000"),
            "shirt_setup": cost("Shirt Procurement / Setup", C.OTHER, U.JOB, "350.0000"),
            "dtf_setup": cost("A4 DTF Batch Setup", C.MACHINE, U.JOB, "2020.0000"),
            "packaging106": cost("Packaging – Shirt/Mug", C.PACKAGING, U.PIECE, "1.0600"),
            "electricity_piece": cost("Electricity – Piece Production", C.ELECTRICITY, U.PIECE, "1.0000"),
            "manpower_piece": cost("Manpower – Piece Production", C.MANPOWER, U.PIECE, "5.0000"),
            "mug": cost("White Mug", C.MATERIAL, U.PIECE, "37.0000"),
            "mug_setup": cost("Mug Procurement / Setup", C.OTHER, U.JOB, "350.0000"),
            "sublimation_setup": cost("Sublimation Print Setup", C.MACHINE, U.JOB, "892.0000"),
            "tote_fabric": cost("Oxford Fabric – Tote Batch", C.MATERIAL, U.JOB, "4470.0000"),
            "tote_dtf": cost("Tote DTF Batch", C.MACHINE, U.JOB, "1700.0000"),
            "packaging08": cost("Tote Packaging", C.PACKAGING, U.PIECE, "0.8000"),
            "sewing": cost("Sewing Labor", C.MANPOWER, U.PIECE, "43.0000"),
            "pen": cost("Blank Pen", C.MATERIAL, U.PIECE, "6.4000"),
            "uv": cost("UV Print", C.MACHINE, U.PIECE, "7.0000"),
            "uv_setup": cost("UV Batch Setup", C.MACHINE, U.JOB, "750.0000"),
            "fan": cost("Foldable Fan", C.MATERIAL, U.PIECE, "9.8000"),
            "fan_dtf": cost("Fan DTF Print", C.MACHINE, U.PIECE, "9.0000"),
            "adfan_paper": cost("Advertising Fan Paper", C.MATERIAL, U.PIECE, "2.8400"),
            "adfan_print": cost("Advertising Fan Print", C.MACHINE, U.PIECE, "6.0000"),
            "adfan_cut": cost("Advertising Fan Cutting", C.MACHINE, U.PIECE, "1.0000"),
            "adfan_lam": cost("Advertising Fan Lamination", C.LAMINATE, U.PIECE, "10.0000"),
            "adfan_handle": cost("Advertising Fan Handle", C.FINISHING, U.PIECE, "2.5000"),
            "adfan_pack": cost("Advertising Fan Packaging", C.PACKAGING, U.PIECE, "10.6000"),
        }

        products = [
            ("Tarpaulin", "AREA", 25, 15, "tarp", []),
            ("Blockout Tarp", "AREA", 40, 35, "blockout", []),
            ("Panaflex", "AREA", 100, 75, "panaflex", []),
            ("Hologram Sticker", "AREA", 120, 110, "hologram", []),
            ("Vinyl Sticker", "AREA", 75, 65, "vinyl", []),
            ("Vinyl Sticker with Laminating", "AREA", 90, 75, "vinyl", ["laminate"]),
            ("Sticker on Sintra 1.5mm", "AREA", 175, 165, "vinyl", ["sintra15", "laminate"]),
            ("Sticker on Sintra 3mm", "AREA", 200, 175, "vinyl", ["sintra3", "laminate"]),
            ("Sticker on Sintra 3mm Hologram", "AREA", 220, 195, "hologram", ["sintra3", "laminate"]),
            ("Sticker on Sintra 5mm", "AREA", 220, 195, "vinyl", ["sintra5", "laminate"]),
            ("Foam Board with Sticker", "AREA", 200, 175, "vinyl", ["foam", "laminate"]),
            ("Acrylic with Print 1.5mm", "AREA", 500, 550, "vinyl", ["acrylic15"]),
            ("Acrylic with Print 3mm", "AREA", 865, 720, "vinyl", ["acrylic3"]),
        ]
        common_area = ["ink", "electricity_area", "manpower_area", "printer", "cutter_area"]
        for name, pricing_type, walk_in, tie_up, media, extras in products:
            product, _ = Product.objects.update_or_create(
                name=name,
                defaults={
                    "pricing_type": pricing_type,
                    "walk_in_rate": walk_in,
                    "tie_up_rate": tie_up,
                    "buffer_percent": 5,
                    "active": True,
                },
            )
            recipe = [media, *extras, *common_area]
            for sequence, key in enumerate(recipe, start=1):
                ProductCostComponent.objects.update_or_create(
                    product=product,
                    cost_item=items[key],
                    basis=ProductCostComponent.Basis.AREA,
                    defaults={"usage_quantity": 1, "sequence": sequence * 10},
                )

        piece_products = [
            ("Tshirt 1 side A4 DTF Print", 250, 200, [("shirt", "PIECE"), ("shirt_setup", "FIXED"), ("dtf_setup", "FIXED"), ("packaging106", "PIECE"), ("electricity_piece", "PIECE"), ("manpower_piece", "PIECE")]),
            ("Sublimation Mug", 85, 75, [("mug", "PIECE"), ("mug_setup", "FIXED"), ("sublimation_setup", "FIXED"), ("packaging106", "PIECE"), ("electricity_piece", "PIECE"), ("manpower_piece", "PIECE")]),
            ("Tote Bag B2B Print DTF", 200, 160, [("tote_fabric", "FIXED"), ("tote_dtf", "FIXED"), ("packaging08", "PIECE"), ("electricity_piece", "PIECE"), ("manpower_piece", "PIECE"), ("sewing", "PIECE")]),
            ("Pen with UV Print", 35, 25, [("pen", "PIECE"), ("uv", "PIECE"), ("uv_setup", "FIXED")]),
            ("Foldable Fan", 35, 25, [("fan", "PIECE"), ("fan_dtf", "PIECE")]),
            ("Advertising Fan B2B", 75, 65, [("adfan_paper", "PIECE"), ("adfan_print", "PIECE"), ("adfan_cut", "PIECE"), ("adfan_lam", "PIECE"), ("adfan_handle", "PIECE"), ("adfan_pack", "PIECE")]),
        ]
        for name, walk_in, tie_up, recipe in piece_products:
            product, _ = Product.objects.update_or_create(
                name=name,
                defaults={
                    "pricing_type": Product.PricingType.PIECE,
                    "walk_in_rate": walk_in,
                    "tie_up_rate": tie_up,
                    "buffer_percent": 0,
                    "active": True,
                },
            )
            for sequence, (key, basis) in enumerate(recipe, start=1):
                ProductCostComponent.objects.update_or_create(
                    product=product,
                    cost_item=items[key],
                    basis=basis,
                    defaults={"usage_quantity": 1, "sequence": sequence * 10},
                )

        Client.objects.get_or_create(name="Walk-In Customer", defaults={"notes": "General counter customer"})
        self.stdout.write(self.style.SUCCESS("360 A.D starter data loaded."))
