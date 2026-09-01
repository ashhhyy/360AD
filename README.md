# 360 A.D Pricing & Quotation CRM

Admin-only MVP for managing clients, materials and production costs, sellable products, itemized cost recipes, quotations, gross profit, and Excel exports.

## Included in this version

- Admin-only authentication; every application screen requires a staff account.
- Client CRUD.
- Material and production cost CRUD for sticker, laminate, board, ink, electricity, manpower, machines, finishing, installation, packaging, and custom costs.
- Sellable product CRUD with separate Walk-In and Tie-Up rates.
- Itemized cost recipes with area, piece, or fixed-per-job calculation bases.
- Saved quotation headers and line items.
- Permanent quotation cost snapshots.
- True cost, selling price, gross profit, GP margin, VAT, and grand total.
- Excel export for individual quotations and all master data.
- Starter data based on `Copy of 360AD Pricing Calculator.xlsx`.
- SQLite locally and PostgreSQL through `DATABASE_URL` when hosted.

Sales accounts are intentionally not part of this MVP. They can be added later after permissions are approved.

## Run locally

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
python manage.py migrate
python manage.py seed_360ad
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000` and sign in with the superuser you created.

## Free deployment

Recommended free MVP setup:

1. Push this project to a free GitHub repository.
2. Create a free Neon PostgreSQL database and copy its connection string.
3. Create a free Render Web Service using `render.yaml`.
4. Set `DATABASE_URL` to the Neon connection string.
5. Set `ADMIN_EMAIL` and a strong `ADMIN_PASSWORD` in Render's environment variables. The build creates the Admin account automatically.

Render's free web service sleeps when idle. Neon is used because Render's local filesystem is temporary and must not store the production SQLite database.

## Calculation rules

For area-based products:

```text
Area per piece = width × height
Pricing quantity = area per piece × quantity
Component cost = pricing quantity × recipe usage × component unit cost
```

For piece-based products:

```text
Component cost = quantity × recipe usage × component unit cost
```

Fixed components are charged once per quotation line. The product buffer is then added as a separate cost snapshot line.

```text
Gross Profit = Selling Price before VAT − True Cost
GP Margin % = Gross Profit ÷ Selling Price before VAT
```

VAT is not included in gross profit.

## Important pricing review

The starter data preserves the workbook's current selling rates, but production recipes are now itemized from the Materials sheet. Review these records before using the app for live customer prices:

- Materials & Costs
- Sellable Products
- Each product's Cost Recipe

The attached workbook contains differences between aggregate PRICING costs and itemized MATERIALS costs, so the website treats the itemized recipe as the source of truth.
